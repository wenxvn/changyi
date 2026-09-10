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
import type { EvidenceDataset, EvidencePayload } from "../types/api";

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
  return (
    <>
      <div className="trust-page__hero">
        <div>
          <span className="eyebrow">TRUST LAYER · PROVISIONAL EVALUATION</span>
          <h1>AI 应该知道，<br /><em>什么时候不该给出答案。</em></h1>
          <p>{evidence.disclaimer}</p>
        </div>
        <div className="trust-page__hero-note">
          <div className="trust-page__hero-note-icon"><LockKeyhole size={20} strokeWidth={1.5} aria-hidden="true" /></div>
          <strong>阶段性证据，不代表临床验证</strong>
          <span>把安全评估、模型指标、数据质量和版本号放在同一处，方便复核与回滚。</span>
          <StatusPill tone="warning">{evidence.status === "provisional" ? "原型阶段" : evidence.status}</StatusPill>
        </div>
      </div>

      <div className="trust-notice" role="note">
        <TriangleAlert size={19} aria-hidden="true" />
        <div>
          <strong>这里展示的是系统证据，不是医学结论。</strong>
          <span>所有指标均来自当前代码仓库中的离线评测与数据报告；不能替代医生诊断、急救指令、处方或临床决策。</span>
        </div>
      </div>

      <section className="trust-evidence-section" aria-labelledby="safety-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">01 · SAFETY FIRST</span><h2 id="safety-evidence-title">先看它能否识别不该耽误的情况。</h2></div>
          <StatusPill tone={evidence.safety.available ? "success" : "danger"}>{evidence.safety.available ? "评测已载入" : "评测不可用"}</StatusPill>
        </div>
        <div className="trust-evidence-grid">
          <article className="evidence-panel evidence-panel--accent">
            <div className="evidence-panel__topline"><ShieldCheck size={19} aria-hidden="true" /><span>{evidence.safety.label}</span></div>
            <div className="evidence-metric-grid">
              <EvidenceMetric label="红旗召回率" value={formatPercent(evidence.safety.red_flag_recall)} note={`${formatCount(evidence.safety.red_flag_count)} 个红旗样例`} />
              <EvidenceMetric label="急症漏检" value={formatCount(evidence.safety.emergency_false_negative)} note="个；越低越好，需结合样例复核" />
              <EvidenceMetric label="低估分诊率" value={formatPercent(evidence.safety.under_triage_rate)} />
              <EvidenceMetric label="评测样例" value={formatCount(evidence.safety.case_count)} note={`其中 ${formatCount(evidence.safety.insufficient_information_count)} 个信息不足`} />
            </div>
            <p className="evidence-panel__footnote">评测结果用于发现风险，不作为发布放行条件。当前需人工复核 {evidence.safety.review_required.length} 个样例。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><CircleAlert size={19} aria-hidden="true" /><span>仍需关注的边界</span></div>
            {evidence.safety.review_required.length > 0 ? (
              <ul className="evidence-review-list">
                {evidence.safety.review_required.slice(0, 6).map((item) => <li key={item}>{item}</li>)}
              </ul>
            ) : <p className="evidence-empty-copy"><Check size={16} aria-hidden="true" /> 当前报告没有列出待复核样例。</p>}
            <p className="evidence-panel__footnote">报告来源：{evidence.safety.report_source}</p>
          </article>
        </div>
      </section>

      <section className="trust-evidence-section" aria-labelledby="model-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">02 · MODEL & DATA</span><h2 id="model-evidence-title">指标必须带着数据范围一起看。</h2></div>
          <StatusPill tone={evidence.model.available ? "neutral" : "danger"}>{evidence.model.available ? evidence.model.model_type : "模型证据不可用"}</StatusPill>
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
            <p className="evidence-panel__footnote">{evidence.model.evaluation_scope}。类别 {formatCount(evidence.model.class_count)} 个，词表 {formatCount(evidence.model.vocabulary_size)} 个。</p>
          </article>
          <article className="evidence-panel">
            <div className="evidence-panel__topline"><Database size={19} aria-hidden="true" /><span>来源与数据指纹</span></div>
            <SourceRow source={evidence.model.model_source} label="模型文件" />
            <SourceRow source={evidence.model.training_data_source} label="训练数据" />
            <SourceRow source={evidence.region.source} label={`区域包 · ${evidence.region.code}`} />
          </article>
        </div>
      </section>

      <section className="trust-evidence-section" aria-labelledby="quality-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">03 · PROVENANCE</span><h2 id="quality-evidence-title">数据质量是限制条件，不是装饰。</h2></div>
          <StatusPill tone={evidence.data_quality.status === "clean" ? "success" : "warning"}>{evidence.data_quality.status === "clean" ? "无已登记问题" : "存在已登记问题"}</StatusPill>
        </div>
        <div className="evidence-quality-panel">
          <div className="evidence-quality-panel__summary">
            <EvidenceMetric label="数据集条目" value={formatCount(evidence.data_quality.dataset_count)} />
            <EvidenceMetric label="已登记问题" value={formatCount(evidence.data_quality.issue_count)} note="不等于临床风险计数" />
            <EvidenceMetric label="区域包" value={evidence.region.pack_version} />
          </div>
          <p className="evidence-panel__footnote">质量报告：{evidence.data_quality.report_source} · schema {evidence.data_quality.schema_version}</p>
        </div>
      </section>

      <section className="trust-evidence-section" aria-labelledby="version-evidence-title">
        <div className="trust-section__heading">
          <div><span className="eyebrow">04 · REPRODUCIBILITY</span><h2 id="version-evidence-title">知道当前运行的，才能知道如何回滚。</h2></div>
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
          {visibleManifest.map((item) => <SourceRow key={item.path} source={item} label={item.format} />)}
          {evidence.dataset_manifest.length > visibleManifest.length ? <p className="evidence-panel__footnote">已显示前 {visibleManifest.length} 条，共 {evidence.dataset_manifest.length} 条；完整清单由 `/api/v1/evidence` 返回。</p> : null}
        </div>
      </section>

      <section className="trust-limitations" aria-labelledby="limitations-title">
        <div><span className="eyebrow">KNOWN LIMITATIONS</span><h2 id="limitations-title">把不确定性留在页面上。</h2></div>
        <ul>{evidence.limitations.map((item) => <li key={item}><TriangleAlert size={16} aria-hidden="true" />{item}</li>)}</ul>
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
