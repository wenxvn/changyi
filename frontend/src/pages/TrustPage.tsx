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

function humanizeLimitation(value: string): string {
  if (value.includes("review_required")) return "固定评估样例仍需保留专业复核，不能据此作为放行依据。";
  if (value.includes("migration_pending")) return "部分医院资料仍在核验，来源、许可和更新时间还不完整。";
  if (value.includes("public_source_mixed")) return "医生资料来源不完全一致，不能据此判断临床适配或疗效。";
  return value.replace("prototype/offline evaluation", "当前离线研究与演示评估");
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
        <code>{source?.path ?? "来源暂未登记"}</code>
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
          <p>{evidence.disclaimer}</p>
        </div>
        <div className="trust-page__hero-note">
          <div className="trust-page__hero-note-icon"><LockKeyhole size={18} strokeWidth={1.6} aria-hidden="true" /></div>
          <strong>研究与演示阶段</strong>
          <span>这些信息帮助理解系统边界与资料来源。</span>
          <StatusPill tone="warning">{evidence.status === "provisional" ? "研究与演示" : evidence.status}</StatusPill>
        </div>
      </div>

      <div className="trust-notice" role="note">
        <TriangleAlert size={19} aria-hidden="true" />
        <div>
          <strong>这里展示的是系统证据，不是医学结论。</strong>
          <span>以下指标来自系统当前离线评估结果，仅用于说明模型与安全边界；不能替代医生诊断、急救指令、处方或临床决策。</span>
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
            <p className="evidence-panel__footnote">评估用于发现风险，不代表临床验证。当前有 {evidence.safety.review_required.length} 个样例需要进一步复核。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><CircleAlert size={19} aria-hidden="true" /><span>仍需关注的边界</span></div>
            {evidence.safety.review_required.length > 0 ? (
              <p className="evidence-review-copy">当前有 {evidence.safety.review_required.length} 个评估样例需要专业复核；具体记录保留在技术详情中。</p>
            ) : <p className="evidence-empty-copy"><Check size={16} aria-hidden="true" /> 当前报告没有列出待复核样例。</p>}
            <p className="evidence-panel__footnote">评估记录会保留样例、时间和结果，便于后续复核。</p>
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
            <p className="evidence-panel__footnote">当前为离线样本切分评估，仅用于研究与演示。类别 {formatCount(evidence.model.class_count)} 个，词表 {formatCount(evidence.model.vocabulary_size)} 个。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><Database size={19} aria-hidden="true" /><span>数据范围与来源</span></div>
            <p className="evidence-panel__plain-copy">评估使用已接入的常州公开医疗与交通资源。医院和医生资料会显示来源状态与更新时间，具体使用前请以机构公开信息为准。</p>
            {evidence.hospital_data ? (
              <div className="evidence-panel__footnote">
                医院目录：{evidence.hospital_data.status} · {evidence.hospital_data.record_count} 条 · 派生能力字段 {Object.keys(evidence.hospital_data.derived_fields).length} 项 · 未支持字段 {evidence.hospital_data.unsupported_fields.join("、") || "无"}。
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
                    offline prototype evaluation，not clinical validation。Jaccard ≥ {groupedCV.jaccard_threshold} 的同标签 component 整组进入同一折；
                    Seed {groupedCV.seed}。Mean/std 与按验证行数加权结果均写入评估报告，不可与随机切分准确率直接横向比较。
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
          <div><span className="eyebrow">03 · 数据质量</span><h2 id="quality-evidence-title">数据质量是限制条件，不是装饰。</h2></div>
          <StatusPill tone={evidence.data_quality.status === "clean" ? "success" : "warning"}>{evidence.data_quality.status === "clean" ? "无已登记问题" : "存在已登记问题"}</StatusPill>
        </div>
        <div className="evidence-quality-panel">
          <div className="evidence-quality-panel__summary">
            <EvidenceMetric label="数据集条目" value={formatCount(evidence.data_quality.dataset_count)} />
            <EvidenceMetric label="已登记问题" value={formatCount(evidence.data_quality.issue_count)} note="不等于临床风险计数" />
            <EvidenceMetric label="服务区域" value={`常州 ${evidence.region.code}`} />
          </div>
          <p className="evidence-panel__footnote">资料质量问题会被登记并保留，不会被静默修正为“已核实”。</p>
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
        <div><span className="eyebrow">已知边界</span><h2 id="limitations-title">把不确定性留在页面上。</h2></div>
        <ul>{evidence.limitations.map((item) => <li key={item}><TriangleAlert size={16} aria-hidden="true" />{humanizeLimitation(item)}</li>)}</ul>
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
