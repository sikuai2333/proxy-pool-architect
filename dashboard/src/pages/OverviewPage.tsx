import { useEffect, useRef, useState } from "react";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MetricCard } from "../components/dashboard/MetricCard";
import { useI18n, type TranslationKey } from "../i18n";
import { dashboardApi } from "../lib/api-client";
import type { OverviewData } from "../types";

const OVERVIEW_REFRESH_MS = 5000;
const OVERVIEW_INITIAL_LOAD_GUARD_MS = 5000;

export function OverviewPage() {
  const { t, language, formatDateTime, formatLatency, formatNumber, formatPercent } = useI18n();
  const [data, setData] = useState<OverviewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const hasDataRef = useRef(false);
  const inFlightRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let initialSettled = false;
    const initialLoadGuard = globalThis.setTimeout(() => {
      if (!cancelled && !initialSettled) {
        setError(t("overview.loadError"));
        setLoading(false);
      }
    }, OVERVIEW_INITIAL_LOAD_GUARD_MS);

    async function load(initial = false) {
      if (inFlightRef.current) {
        return;
      }

      inFlightRef.current = true;
      if (initial) {
        setLoading(true);
        setError(null);
      }
      try {
        const overview = await dashboardApi.getOverview();
        if (!cancelled) {
          setData(overview);
          setError(null);
          setRefreshError(null);
          setLastUpdatedAt(new Date().toISOString());
          hasDataRef.current = true;
        }
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : t("overview.loadError");
          if (hasDataRef.current) {
            setRefreshError(message);
          } else {
            setError(message);
          }
        }
      } finally {
        if (!cancelled) {
          if (initial) {
            initialSettled = true;
            globalThis.clearTimeout(initialLoadGuard);
            setLoading(false);
          }
        }
        inFlightRef.current = false;
      }
    }

    void load(true);
    const timer = globalThis.setInterval(() => {
      void load(false);
    }, OVERVIEW_REFRESH_MS);

    return () => {
      cancelled = true;
      globalThis.clearTimeout(initialLoadGuard);
      globalThis.clearInterval(timer);
    };
  }, [language]);

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
      <section className="panel panel-note">
        <h2>{t("overview.liveUpdates")}</h2>
        <p>
          {t("overview.autoRefresh", {
            seconds: formatNumber(OVERVIEW_REFRESH_MS / 1000),
            updatedAt: formatDateTime(lastUpdatedAt)
          })}
        </p>
        {refreshError ? <p className="inline-status inline-status-warning">{refreshError}</p> : null}
      </section>

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
              <span>{t("overview.database")}</span>
              <strong className={`status-text status-${stats.db_status}`}>
                {t(`status.${stats.db_status}` as TranslationKey)}
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
