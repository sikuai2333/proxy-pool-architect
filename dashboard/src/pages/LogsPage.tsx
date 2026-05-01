import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { EventLogTable } from "../components/logs/EventLogTable";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { EventLogEntry } from "../types";

export function LogsPage() {
  const [items, setItems] = useState<EventLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const events = await dashboardApi.listEvents();
        if (!cancelled) {
          setItems(events);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load event log");
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
    return <LoadingState label="Loading event log" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (items.length === 0) {
    return <EmptyState title="No events available" message="No operational events were returned." />;
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>Operational events</h2>
        <p>
          {dashboardDataMode === "live"
            ? "Live mode reads backend event history and falls back to mock entries only when the endpoint is unavailable."
            : "This page is currently backed by mock operational events."}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Recent events</h2>
            <p>Warnings, errors, and routine operator-visible actions.</p>
          </div>
        </div>
        <EventLogTable items={items} />
      </section>
    </div>
  );
}
