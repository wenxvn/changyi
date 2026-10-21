import { useEffect, useState } from "react";
import {
  ArrowRight,
  Check,
  CircleAlert,
  Database,
  GitBranch,
  LoaderCircle,
  LockKeyhole,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { ApiError } from "../api/client";
import { getEvidence } from "../api/evidence";
import { Button } from "../components/ui/Button";
import { StatusPill } from "../components/ui/StatusPill";
import type { EvidenceDataset, EvidencePayload, ModelSplitMetrics } from "../types/api";

function errorFor(reason: unknown): ApiError {
  return reason instanceof ApiError
    ? reason
    : new ApiError("NETWORK_ERROR", "可信证据暂时无法载入，请稍后重试。");
}

function formatCount(value: number | null): string {
  return value === null ? "未提供" : value.toLocaleString("zh-CN");
}

function formatPercent(value: number | null): string {
  return value === null ? "未提供" : `${(value * 100).toFixed(2)}%`;
}

function shortHash(value: string): string {
  return value.length > 18 ? `${value.slice(0, 12)}…${value.slice(-6)}` : value;
}

function safetyLabel(available: boolean): string {
  return available ? "安全评估结果" : "安全评估不可用";
}

function splitMetricValue(value: number | null | undefined): string {
  return value === null || value === undefined ? "未提供" : formatPercent(value);
}

function EvidenceMetric({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="evidence-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note ? <small>{note}</small> : null}
    </div>
  );
}

function SourceRow({ source, label }: { source: EvidenceDataset | null; label: string }) {
  return (
    <div className="evidence-source-row">
      <div>
        <span className="evidence-source-row__label">{label}</span>
        <code>{source?.path ?? "未提供"}</code>
      </div>
      <span className="evidence-source-row__hash" title={source?.sha256 ?? undefined}>
        SHA-256 · {source ? shortHash(source.sha256) : "未提供"}
      </span>
    </div>
  );
}

function TrustContent({ evidence, onNavigate }: { evidence: EvidencePayload; onNavigate: (path: string) => void }) {
  const visibleManifest = evidence.dataset_manifest.slice(0, 8);
  const modelSplits: Array<{ label: string; metrics: ModelSplitMetrics | undefined; note?: string }> = [
    { label: "随机基线", metrics: evidence.model.random_baseline, note: "宽松参考，可能受近重复样本影响。" },
    { label: "严格 fingerprint 分组", metrics: evidence.model.grouped_fingerprint, note: "保证完全相同症状集合不跨 split。" },
    { label: "严格近重复隔离（同标签）", metrics: evidence.model.near_duplicate_same_label, note: "测试子集仅覆盖部分疾病类别，不能与随机切分准确率直接横向比较。" },
    { label: "近重复全局分组（对照）", metrics: evidence.model.near_duplicate_global, note: "对照：跨疾病高相似样本也会被连接，可能形成更大 component。" },
  ].filter((item) => Boolean(item.metrics));
  const strictIsolation = evidence.model.strict_near_duplicate_isolation;
  const groupedCV = evidence.model.near_duplicate_grouped_cv;
  const cvTop1 = groupedCV?.aggregate?.top1_accuracy;
  return (
    <>
      <div className="trust-page__hero">
        <div>
          <span className="eyebrow">可信信息 · 系统评估</span>
          <h1>AI 应该知道，<em>什么时候不该给出答案。</em></h1>
          <p>以下展示系统在固定样例和离线数据上的评估结果，用于说明能力边界，不替代医生判断。</p>
        </div>
        <div className="trust-page__hero-note">
          <div className="trust-page__hero-note-icon"><LockKeyhole size={18} strokeWidth={1.6} aria-hidden="true" /></div>
          <strong>持续评估</strong>
          <span>理解系统能力与适用边界。</span>
          <StatusPill tone="warning">持续评估</StatusPill>
        </div>
      </div>

      <div className="trust-notice" role="note">
        <TriangleAlert size={19} aria-hidden="true" />
        <div>
          <strong>这里展示的是系统证据，不是医学结论。</strong>
          <span>以下结果来自固定样例与离线数据，用于说明模型与安全边界；不能替代医生诊断、急救指令、处方或临床决策。</span>
        </div>
      </div>

      <section className="trust-evidence-section" aria-labelledby="safety-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">01 · 安全优先</span><h2 id="safety-evidence-title">先看它能否识别不该耽误的情况。</h2></div>
          <StatusPill tone={evidence.safety.available ? "success" : "danger"}>{evidence.safety.available ? "评测已载入" : "评测不可用"}</StatusPill>
        </div>
        <div className="trust-evidence-grid">
          <article className="evidence-panel evidence-panel--accent">
            <div className="evidence-panel__topline"><ShieldCheck size={19} aria-hidden="true" /><span>{safetyLabel(evidence.safety.available)}</span></div>
            <div className="evidence-metric-grid">
              <EvidenceMetric label="红旗召回率" value={formatPercent(evidence.safety.red_flag_recall)} note={`${formatCount(evidence.safety.red_flag_count)} 个红旗样例`} />
              <EvidenceMetric label="急症漏检" value={formatCount(evidence.safety.emergency_false_negative)} note="个；越低越好，需结合样例复核" />
              <EvidenceMetric label="低估分诊率" value={formatPercent(evidence.safety.under_triage_rate)} />
              <EvidenceMetric label="评测样例" value={formatCount(evidence.safety.case_count)} note={`其中 ${formatCount(evidence.safety.insufficient_information_count)} 个信息不足`} />
            </div>
            <p className="evidence-panel__footnote">评估用于发现风险，不代表临床验证。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><CircleAlert size={19} aria-hidden="true" /><span>使用边界</span></div>
            <p className="evidence-empty-copy"><Check size={16} aria-hidden="true" /> 信息不足时先追问，不强行给出科室方向。</p>
            <p className="evidence-empty-copy"><Check size={16} aria-hidden="true" /> 红旗信号优先于距离、价格和排序偏好。</p>
            <p className="evidence-panel__footnote">固定样例用于工程回归，具体记录保留在技术详情中。</p>
          </article>
        </div>
      </section>

      <section className="trust-evidence-section" aria-labelledby="model-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">02 · 模型与数据</span><h2 id="model-evidence-title">指标必须带着数据范围一起看。</h2></div>
          <StatusPill tone={evidence.model.available ? "neutral" : "danger"}>{evidence.model.available ? "离线样本评估" : "模型证据不可用"}</StatusPill>
        </div>
        <div className="trust-evidence-grid">
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><GitBranch size={19} aria-hidden="true" /><span>{evidence.model.label}</span></div>
            <div className="evidence-metric-grid">
              <EvidenceMetric label="Top-1" value={formatPercent(evidence.model.top1_accuracy)} />
              <EvidenceMetric label="Top-3" value={formatPercent(evidence.model.top3_accuracy)} />
              <EvidenceMetric label="训练样本" value={formatCount(evidence.model.training_rows)} />
              <EvidenceMetric label="测试样本" value={formatCount(evidence.model.test_rows)} />
            </div>
            <p className="evidence-panel__footnote">{evidence.model.label.includes("随机切分基线") ? "随机切分参考可能受近重复样本影响。" : ""}当前为症状—疾病离线样本评估，不能换算为中文主诉的就医科室准确率。类别 {formatCount(evidence.model.class_count)} 个，词表 {formatCount(evidence.model.vocabulary_size)} 个。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><Database size={19} aria-hidden="true" /><span>数据范围与来源</span></div>
            <p className="evidence-panel__plain-copy">模型评估使用症状—疾病离线样本，不是常州患者的中文临床评测。医院、医生与交通资料用于资源目录与排序。</p>
            {evidence.hospital_data ? (
              <div className="evidence-panel__footnote">
                医院目录：{evidence.hospital_data.record_count} 条 · 公开字段 {evidence.hospital_data.public_fact_fields.length} 项。
              </div>
            ) : null}
          </article>
        </div>
        {(modelSplits.length > 0 || groupedCV || strictIsolation) ? (
          <details className="trust-model-details">
            <summary>
              <span>模型切分与近重复隔离</span>
              <small>严格评估用于暴露泛化风险，不可与随机切分横向等价比较</small>
            </summary>
            <div className="trust-model-details__body">
              {(evidence.model.near_duplicate_same_label || evidence.model.random_baseline || evidence.model.grouped_fingerprint) ? (
                <div className="trust-model-comparison">
                  {modelSplits.map(({ label, metrics, note }) => metrics ? (
                    <article className="evidence-panel" key={label}>
                      <div className="evidence-panel__topline"><GitBranch size={17} aria-hidden="true" /><span>{label}</span></div>
                      <div className="evidence-metric-grid">
                        <EvidenceMetric label="Macro-F1" value={splitMetricValue(metrics.macro_f1)} />
                        <EvidenceMetric label="Macro-Recall" value={splitMetricValue(metrics.macro_recall)} />
                        <EvidenceMetric label="覆盖率" value={splitMetricValue(metrics.coverage)} />
                        <EvidenceMetric label="测试样本" value={formatCount(metrics.test_rows)} />
                      </div>
                      <p className="evidence-panel__footnote">
                        Top-1 {splitMetricValue(metrics.accuracy)} · Top-3 {splitMetricValue(metrics.top3_accuracy)}
                        {metrics.cross_split_near_duplicates ? ` · 跨 split 近重复 ${metrics.cross_split_near_duplicates.pair_count} 对` : ""}
                        {note ? `。${note}` : ""}
                      </p>
                    </article>
                  ) : null)}
                </div>
              ) : null}
              {groupedCV ? (
                <article className="evidence-panel trust-strict-isolation">
                  <div className="evidence-panel__topline">
                    <GitBranch size={17} aria-hidden="true" />
                    <span>Grouped Near-Duplicate CV</span>
                  </div>
                  <div className="evidence-metric-grid">
                    <EvidenceMetric label="折数" value={formatCount(groupedCV.fold_count)} note="同一近重复 component 不跨折" />
                    <EvidenceMetric label="Mean Top-1" value={splitMetricValue(cvTop1?.mean ?? null)} />
                    <EvidenceMetric label="Mean Top-3" value={splitMetricValue(groupedCV.aggregate?.top3_accuracy?.mean ?? null)} />
                    <EvidenceMetric label="Mean Macro-F1" value={splitMetricValue(groupedCV.aggregate?.macro_f1?.mean ?? null)} />
                    <EvidenceMetric
                      label="跨折覆盖类别"
                      value={`${formatCount(groupedCV.class_coverage_across_folds?.present_class_count ?? null)} / ${formatCount(groupedCV.class_coverage_across_folds?.total_class_count ?? null)}`}
                    />
                    <EvidenceMetric
                      label="跨 split 近重复"
                      value={formatCount(groupedCV.cross_split_near_duplicates_max_pair_count ?? null)}
                      note="各折最大近重复对数"
                    />
                  </div>
                  <p className="evidence-panel__footnote">
                    近重复样本按 Jaccard 阈值 {groupedCV.jaccard_threshold} 整组进入同一折；Seed {groupedCV.seed}。结果写入评估报告，不与随机切分准确率直接横向比较。
                  </p>
                  <p className="evidence-panel__footnote">
                    严格评估显示疾病分类模型泛化能力有限，因此当前版本不允许该模型单独决定患者就医科室；模型结果仅作为研究型辅助信号展示。
                  </p>
                </article>
              ) : null}
              {strictIsolation ? (
                <article className="evidence-panel trust-strict-isolation">
                  <div className="evidence-panel__topline"><ShieldCheck size={17} aria-hidden="true" /><span>{strictIsolation.label}</span></div>
                  <div className="evidence-metric-grid">
                    <EvidenceMetric label="测试样本" value={formatCount(strictIsolation.test_samples)} />
                    <EvidenceMetric label="覆盖类别" value={`${formatCount(strictIsolation.present_classes)} / ${formatCount(strictIsolation.total_classes)}`} />
                    <EvidenceMetric label="跨 split 近重复" value={formatCount(strictIsolation.cross_split_near_duplicates)} note="Jaccard ≥ 阈值的跨 split 对数" />
                    <EvidenceMetric label="Seed" value={formatCount(strictIsolation.seed)} />
                    <EvidenceMetric label="Jaccard 阈值" value={strictIsolation.jaccard_threshold === null ? "未提供" : String(strictIsolation.jaccard_threshold)} />
                  </div>
                  <p className="evidence-panel__footnote">{strictIsolation.explanation}</p>
                  <p className="evidence-panel__footnote">该指标用于暴露近重复泄漏风险，不是“真实准确率只有 20%”，也不应与随机切分结果等价横向比较。</p>
                </article>
              ) : null}
              {evidence.model.near_duplicate_audit ? (
                <p className="evidence-panel__footnote trust-model-audit">
                  近重复审计：阈值 {evidence.model.near_duplicate_audit.jaccard_threshold}，共 {evidence.model.near_duplicate_audit.pair_count} 对，
                  其中跨疾病 {evidence.model.near_duplicate_audit.cross_label_pair_count} 对。更严格切分可能降低表面指标，但更能反映泛化能力。
                </p>
              ) : null}
            </div>
          </details>
        ) : null}
      </section>

      <section className="trust-evidence-section" aria-labelledby="quality-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">03 · 数据质量</span><h2 id="quality-evidence-title">数据持续校验，结论保持克制。</h2></div>
          <StatusPill tone="neutral">持续校验</StatusPill>
        </div>
        <div className="evidence-quality-panel">
          <div className="evidence-quality-panel__summary">
            <EvidenceMetric label="数据集条目" value={formatCount(evidence.data_quality.dataset_count)} />
            <EvidenceMetric label="服务区域" value={`常州 ${evidence.region.code}`} />
          </div>
          <p className="evidence-panel__footnote">资料按批次校验并持续更新。</p>
        </div>
      </section>

      <details className="trust-technical-details">
        <summary><span>技术详情</span><small>版本、校验信息与完整资料记录</small></summary>
        <section className="trust-evidence-section trust-evidence-section--technical" aria-labelledby="version-evidence-title">
          <div className="trust-section__heading">
            <div><span className="eyebrow">04 · 技术详情</span><h2 id="version-evidence-title">每一次判断，都应该可以追溯到明确的版本。</h2></div>
          </div>
          <div className="trust-version-grid">
            {Object.entries({
              应用: evidence.versions.app,
              排序: evidence.versions.ranking,
              分诊规则: evidence.versions.triage_rules,
              模型: evidence.versions.model,
              数据集: evidence.versions.dataset,
            }).map(([label, value]) => <div className="trust-version" key={label}><span>{label}</span><code>{value}</code></div>)}
          </div>
          <div className="evidence-manifest">
            <div className="evidence-panel__topline"><Database size={19} aria-hidden="true" /><span>数据集清单 · SHA-256</span></div>
            <SourceRow source={evidence.model.model_source} label="模型文件" />
            <SourceRow source={evidence.model.training_data_source} label="训练数据" />
            <SourceRow source={evidence.region.source} label={`区域包 · ${evidence.region.code}`} />
            {visibleManifest.map((item) => <SourceRow key={item.path} source={item} label={item.format} />)}
            {evidence.dataset_manifest.length > visibleManifest.length ? <p className="evidence-panel__footnote">已显示前 {visibleManifest.length} 条，共 {evidence.dataset_manifest.length} 条；完整清单由系统证据记录返回。</p> : null}
          </div>
        </section>
      </details>

      <section className="trust-limitations" aria-labelledby="limitations-title">
        <div><span className="eyebrow">已知边界</span><h2 id="limitations-title">清楚说明适用范围。</h2></div>
        <ul>
          <li><TriangleAlert size={16} aria-hidden="true" />固定样例与离线数据用于工程回归，不等同于临床验证。</li>
          <li><TriangleAlert size={16} aria-hidden="true" />科室方向与模型结果仅作辅助参考，不替代医生面诊。</li>
          <li><TriangleAlert size={16} aria-hidden="true" />交通与距离为估算，实际路线以导航和现场情况为准。</li>
        </ul>
      </section>

      <div className="trust-page__footer-note"><span>想查看这些证据对应的资源和就医路径？</span><Button variant="secondary" onClick={() => onNavigate("/resources")} icon={<ArrowRight size={16} aria-hidden="true" />}>查看医疗资源</Button></div>
    </>
  );
}

export function TrustPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  const [evidence, setEvidence] = useState<EvidencePayload | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getEvidence(controller.signal)
      .then((payload) => {
        if (controller.signal.aborted) return;
        setEvidence(payload);
        setError(null);
      })
      .catch((reason) => {
        if (!controller.signal.aborted) setError(errorFor(reason));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt]);

  return (
    <section className="trust-page page-container">
      {loading ? <div className="trust-loading" aria-live="polite"><LoaderCircle className="spin" size={18} aria-hidden="true" /> 正在读取评测与数据证据…</div> : null}
      {!loading && error ? <div className="trust-error" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{error.message}</span><button type="button" onClick={() => setAttempt((value) => value + 1)}>重试</button></div> : null}
      {!loading && !error && evidence ? <TrustContent evidence={evidence} onNavigate={onNavigate} /> : null}
    </section>
  );
}
