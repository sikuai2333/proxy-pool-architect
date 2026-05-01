import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { PaginationControls } from "../components/common/PaginationControls";
import { EventLogTable } from "../components/logs/EventLogTable";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { EventLogEntry, PaginatedResponse } from "../types";

const PAGE_SIZE = 20;

function buildListMessage(
  response: PaginatedResponse<EventLogEntry> | null,
  formatNumber: (value: number) => string,
  t: ReturnType<typeof useI18n>["t"]
) {
  if (!response || response.total === 0) {
    return t("logs.emptyMessage");
  }

  const start = response.offset + 1;
  const end = response.offset + response.items.length;
  return t("common.listRange", {
    start: formatNumber(start),
    end: formatNumber(end),
    total: formatNumber(response.total)
  });
}

export function LogsPage() {
  const { t, language, formatNumber } = useI18n();
  const [data, setData] = useState<PaginatedResponse<EventLogEntry> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const events = await dashboardApi.listEvents(PAGE_SIZE, (page - 1) * PAGE_SIZE);
        if (!cancelled) {
          if (events.items.length === 0 && events.total > 0 && page > 1) {
            setPage((current) => Math.max(1, current - 1));
            return;
          }
          setData(events);
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
  }, [language, page]);

  if (loading) {
    return <LoadingState label={t("logs.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data || data.items.length === 0) {
    return <EmptyState title={t("logs.emptyTitle")} message={t("logs.emptyMessage")} />;
  }

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

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
            <p>{buildListMessage(data, formatNumber, t)}</p>
          </div>
          <PaginationControls
            ariaLabel={t("logs.paginationLabel")}
            page={page}
            totalPages={totalPages}
            disabled={loading}
            onPrevious={() => setPage((current) => Math.max(1, current - 1))}
            onNext={() => setPage((current) => Math.min(totalPages, current + 1))}
          />
        </div>
        <EventLogTable items={data.items} />
      </section>
    </div>
  );
}
