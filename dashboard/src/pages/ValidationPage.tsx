import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MetricCard } from "../components/dashboard/MetricCard";
import { ValidationJobTable } from "../components/validation/ValidationJobTable";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { EventLogEntry, OverviewData, ValidationJob } from "../types";

function countErrorTypes(events: EventLogEntry[]) {
  const counts = new Map<string, number>();
  events.forEach((event) => {
    if (event.level === "warning" || event.level === "error") {
      counts.set(event.type, (counts.get(event.type) ?? 0) + 1);
    }
  });

  return [...counts.entries()]
    .map(([type, total]) => ({ type, total }))
    .sort((left, right) => right.total - left.total);
}

export function ValidationPage() {
  const { t, formatNumber, formatPercent } = useI18n();
  const [jobs, setJobs] = useState<ValidationJob[]>([]);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [events, setEvents] = useState<EventLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [validationJobs, nextOverview, nextEvents] = await Promise.all([
          dashboardApi.listValidationJobs(),
          dashboardApi.getOverview(),
          dashboardApi.listEvents()
        ]);
        if (!cancelled) {
          setJobs(validationJobs);
          setOverview(nextOverview);
          setEvents(nextEvents);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("validation.loadError"));
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
    return <LoadingState label={t("validation.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (jobs.length === 0 || !overview) {
    return <EmptyState title={t("validation.emptyTitle")} message={t("validation.emptyMessage")} />;
  }

  const totalChecked = jobs.reduce((sum, item) => sum + item.checked_count, 0);
  const totalSuccess = jobs.reduce((sum, item) => sum + item.success_count, 0);
  const totalTimeout = jobs.reduce((sum, item) => sum + item.timeout_count, 0);
  const errorTypes = countErrorTypes(events);

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("validation.statusTitle")}</h2>
        <p>
          {dashboardDataMode === "live"
            ? t("validation.liveNote")
            : t("validation.mockNote")}
        </p>
      </section>

      <section className="metric-section">
        <MetricCard
          label={t("validation.recentSuccessRate")}
          value={formatPercent(totalChecked > 0 ? totalSuccess / totalChecked : null)}
          detail={t("validation.recentSuccessDetail")}
          tone="good"
        />
        <MetricCard
          label={t("validation.timeoutRate")}
          value={formatPercent(totalChecked > 0 ? totalTimeout / totalChecked : null)}
          detail={t("validation.timeoutEvents", { count: formatNumber(totalTimeout) })}
          tone="warning"
        />
        <MetricCard
          label={t("overview.deadProxies")}
          value={formatNumber(overview.stats.dead)}
          detail={t("validation.deadDetail")}
          tone="danger"
        />
        <MetricCard
          label={t("overview.checkedProxies")}
          value={formatNumber(overview.stats.checked)}
          detail={t("validation.checkedDetail")}
          tone="good"
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("validation.recentJobs")}</h2>
            <p>{t("validation.jobsDescription")}</p>
          </div>
        </div>
        <ValidationJobTable items={jobs} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("validation.commonErrors")}</h2>
            <p>{t("validation.commonErrorsDescription")}</p>
          </div>
        </div>
        <div className="stack-list">
          {errorTypes.slice(0, 5).map((item) => (
            <div key={item.type} className="stack-row">
              <div className="stack-row-header">
                <strong>{item.type}</strong>
                <span>{t("validation.eventsCount", { count: formatNumber(item.total) })}</span>
              </div>
              <div className="stack-track" aria-hidden="true">
                <div className="stack-fill stack-fill-warning" style={{ width: `${Math.max(12, item.total * 18)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
