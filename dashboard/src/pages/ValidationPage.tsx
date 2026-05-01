import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MetricCard } from "../components/dashboard/MetricCard";
import { ValidationJobTable } from "../components/validation/ValidationJobTable";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import { formatNumber, formatPercent } from "../lib/format";
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
          setError(err instanceof Error ? err.message : "Unable to load validation status");
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
  }, []);

  if (loading) {
    return <LoadingState label="Loading validation status" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (jobs.length === 0 || !overview) {
    return <EmptyState title="No validation activity available" message="No recent validation jobs were returned." />;
  }

  const totalChecked = jobs.reduce((sum, item) => sum + item.checked_count, 0);
  const totalSuccess = jobs.reduce((sum, item) => sum + item.success_count, 0);
  const totalTimeout = jobs.reduce((sum, item) => sum + item.timeout_count, 0);
  const errorTypes = countErrorTypes(events);

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>Validation status</h2>
        <p>
          {dashboardDataMode === "live"
            ? "Live mode reads recent validation jobs and operational events from the backend."
            : "This page is currently backed by mock validation history."}
        </p>
      </section>

      <section className="metric-section">
        <MetricCard
          label="Recent success rate"
          value={formatPercent(totalChecked > 0 ? totalSuccess / totalChecked : null)}
          detail="Across recent validation jobs"
          tone="good"
        />
        <MetricCard
          label="Timeout rate"
          value={formatPercent(totalChecked > 0 ? totalTimeout / totalChecked : null)}
          detail={`${formatNumber(totalTimeout)} timeout events`}
          tone="warning"
        />
        <MetricCard
          label="Dead proxies"
          value={formatNumber(overview.stats.dead)}
          detail="Current dead pool size"
          tone="danger"
        />
        <MetricCard
          label="Checked proxies"
          value={formatNumber(overview.stats.checked)}
          detail="Ready for selection"
          tone="good"
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Recent validation jobs</h2>
            <p>Job-level throughput, success, failure, and timeout signals.</p>
          </div>
        </div>
        <ValidationJobTable items={jobs} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Common error types</h2>
            <p>Most frequent warning and error categories from recent events.</p>
          </div>
        </div>
        <div className="stack-list">
          {errorTypes.slice(0, 5).map((item) => (
            <div key={item.type} className="stack-row">
              <div className="stack-row-header">
                <strong>{item.type}</strong>
                <span>{formatNumber(item.total)} events</span>
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
