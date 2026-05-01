import { useEffect, useState } from "react";

import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MetricCard } from "../components/dashboard/MetricCard";
import { dashboardApi } from "../lib/api-client";
import { formatDateTime, formatLatency, formatNumber, formatPercent } from "../lib/format";
import type { OverviewData } from "../types";

export function OverviewPage() {
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
          setError(err instanceof Error ? err.message : "Unexpected dashboard error");
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
    return <LoadingState label="Loading dashboard data" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <ErrorState title="No dashboard data" message="Mock overview payload is empty." />;
  }

  const { stats, health } = data;

  return (
    <div className="overview-page">
      <section className="metric-section" aria-label="Proxy pool counts">
        <MetricCard label="Raw proxies" value={formatNumber(stats.raw)} detail="Awaiting validation" />
        <MetricCard
          label="Checked proxies"
          value={formatNumber(stats.checked)}
          detail="Connectivity passed"
          tone="good"
        />
        <MetricCard
          label="Elite proxies"
          value={formatNumber(stats.elite)}
          detail="Highest quality pool"
          tone="good"
        />
        <MetricCard
          label="Dead proxies"
          value={formatNumber(stats.dead)}
          detail={`${formatNumber(stats.cooldown)} in cooldown`}
          tone="danger"
        />
      </section>

      <section className="overview-grid" aria-label="Operational summary">
        <div className="panel">
          <h2>Performance</h2>
          <div className="summary-list">
            <div>
              <span>Average latency</span>
              <strong>{formatLatency(stats.avg_latency_ms)}</strong>
            </div>
            <div>
              <span>Success rate</span>
              <strong>{formatPercent(stats.success_rate)}</strong>
            </div>
            <div>
              <span>Last fetch</span>
              <strong>{formatDateTime(stats.last_fetch_at)}</strong>
            </div>
            <div>
              <span>Last validation</span>
              <strong>{formatDateTime(stats.last_validate_at)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h2>System health</h2>
          <div className="health-list">
            <div>
              <span>API</span>
              <strong className={`status-text status-${health.status}`}>{health.status}</strong>
            </div>
            <div>
              <span>Redis</span>
              <strong className={`status-text status-${stats.redis_status}`}>
                {stats.redis_status}
              </strong>
            </div>
            <div>
              <span>Scheduler</span>
              <strong className={`status-text status-${stats.scheduler_status}`}>
                {stats.scheduler_status}
              </strong>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
