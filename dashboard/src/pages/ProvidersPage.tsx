import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { PaginationControls } from "../components/common/PaginationControls";
import { ProviderTable } from "../components/providers/ProviderTable";
import { ProviderUrlImportForm } from "../components/providers/ProviderUrlImportForm";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { ProviderSummary } from "../types";

const PAGE_SIZE = 8;

export function ProvidersPage() {
  const { t, language, formatNumber } = useI18n();
  const [items, setItems] = useState<ProviderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  async function loadProviders() {
    setLoading(true);
    setError(null);

    try {
      const providers = await dashboardApi.listProviders();
      setItems(providers);
      setPage(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("providers.loadError"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const providers = await dashboardApi.listProviders();
        if (!cancelled) {
          setItems(providers);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("providers.loadError"));
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
  }, [language]);

  if (loading) {
    return <LoadingState label={t("providers.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const offset = (page - 1) * PAGE_SIZE;
  const visibleItems = items.slice(offset, offset + PAGE_SIZE);

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("providers.health")}</h2>
        <p>
          {dashboardDataMode === "live"
            ? t("providers.liveNote")
            : t("providers.mockNote")}
        </p>
      </section>

      <ProviderUrlImportForm onImported={loadProviders} />

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("providers.inventory")}</h2>
            <p>
              {items.length === 0
                ? t("providers.emptyMessage")
                : t("common.listRange", {
                    start: formatNumber(offset + 1),
                    end: formatNumber(offset + visibleItems.length),
                    total: formatNumber(items.length)
                  })}
            </p>
          </div>
          <PaginationControls
            ariaLabel={t("providers.paginationLabel")}
            page={page}
            totalPages={totalPages}
            disabled={loading || items.length === 0}
            onPrevious={() => setPage((current) => Math.max(1, current - 1))}
            onNext={() => setPage((current) => Math.min(totalPages, current + 1))}
          />
        </div>
        {visibleItems.length === 0 ? (
          <EmptyState title={t("providers.emptyTitle")} message={t("providers.emptyMessage")} />
        ) : (
          <ProviderTable items={visibleItems} />
        )}
      </section>
    </div>
  );
}
