import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { EventLogTable } from "../components/logs/EventLogTable";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { EventLogEntry } from "../types";

export function LogsPage() {
  const { t } = useI18n();
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
          setError(err instanceof Error ? err.message : t("logs.loadError"));
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
    return <LoadingState label={t("logs.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (items.length === 0) {
    return <EmptyState title={t("logs.emptyTitle")} message={t("logs.emptyMessage")} />;
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("logs.operationalEvents")}</h2>
        <p>
          {dashboardDataMode === "live"
            ? t("logs.liveNote")
            : t("logs.mockNote")}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("logs.recentEvents")}</h2>
            <p>{t("logs.description")}</p>
          </div>
        </div>
        <EventLogTable items={items} />
      </section>
    </div>
  );
}
