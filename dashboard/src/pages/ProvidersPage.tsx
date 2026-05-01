import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { ProviderTable } from "../components/providers/ProviderTable";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { ProviderSummary } from "../types";

export function ProvidersPage() {
  const { t } = useI18n();
  const [items, setItems] = useState<ProviderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const providers = await dashboardApi.listProviders();
        if (!cancelled) {
          setItems(providers);
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
  }, [t]);

  if (loading) {
    return <LoadingState label={t("providers.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (items.length === 0) {
    return <EmptyState title={t("providers.emptyTitle")} message={t("providers.emptyMessage")} />;
  }

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

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("providers.inventory")}</h2>
            <p>{t("providers.description")}</p>
          </div>
        </div>
        <ProviderTable items={items} />
      </section>
    </div>
  );
}
