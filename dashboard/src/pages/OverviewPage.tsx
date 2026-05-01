import { useEffect, useState } from "react";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MetricCard } from "../components/dashboard/MetricCard";
import { useI18n, type TranslationKey } from "../i18n";
import { dashboardApi } from "../lib/api-client";
import type { OverviewData } from "../types";

export function OverviewPage() {
  const { t, formatDateTime, formatLatency, formatNumber, formatPercent } = useI18n();
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const overview = await dashboardApi.getOverview();
        if (!cancelled) {
          setData(overview);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("overview.loadError"));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [t]);

  if (loading) {
    return <LoadingState label={t("overview.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <ErrorState title={t("overview.noDataTitle")} message={t("overview.noDataMessage")} />;
  }

  const { stats, health } = data;

  return (
    <div className="overview-page">
      <section className="metric-section" aria-label={t("overview.poolCounts")}>
        <MetricCard label={t("overview.rawProxies")} value={formatNumber(stats.raw)} detail={t("overview.rawDetail")} />
        <MetricCard
          label={t("overview.checkedProxies")}
          value={formatNumber(stats.checked)}
          detail={t("overview.checkedDetail")}
          tone="good"
        />
        <MetricCard
          label={t("overview.eliteProxies")}
          value={formatNumber(stats.elite)}
          detail={t("overview.eliteDetail")}
          tone="good"
        />
        <MetricCard
          label={t("overview.deadProxies")}
          value={formatNumber(stats.dead)}
          detail={t("overview.cooldownDetail", { count: formatNumber(stats.cooldown) })}
          tone="danger"
        />
      </section>

      <section className="overview-grid" aria-label={t("overview.operationalSummary")}>
        <div className="panel">
          <h2>{t("overview.performance")}</h2>
          <div className="summary-list">
            <div>
              <span>{t("overview.averageLatency")}</span>
              <strong>{formatLatency(stats.avg_latency_ms)}</strong>
            </div>
            <div>
              <span>{t("overview.successRate")}</span>
              <strong>{formatPercent(stats.success_rate)}</strong>
            </div>
            <div>
              <span>{t("overview.lastFetch")}</span>
              <strong>{formatDateTime(stats.last_fetch_at)}</strong>
            </div>
            <div>
              <span>{t("overview.lastValidation")}</span>
              <strong>{formatDateTime(stats.last_validate_at)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h2>{t("overview.systemHealth")}</h2>
          <div className="health-list">
            <div>
              <span>{t("overview.api")}</span>
              <strong className={`status-text status-${health.status}`}>
                {t(`status.${health.status}` as TranslationKey)}
              </strong>
            </div>
            <div>
              <span>{t("overview.redis")}</span>
              <strong className={`status-text status-${stats.redis_status}`}>
                {t(`status.${stats.redis_status}` as TranslationKey)}
              </strong>
            </div>
            <div>
              <span>{t("overview.scheduler")}</span>
              <strong className={`status-text status-${stats.scheduler_status}`}>
                {t(`status.${stats.scheduler_status}` as TranslationKey)}
              </strong>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
