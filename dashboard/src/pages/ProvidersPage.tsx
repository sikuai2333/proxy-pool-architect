import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { ProviderTable } from "../components/providers/ProviderTable";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { ProviderSummary } from "../types";

export function ProvidersPage() {
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
          setError(err instanceof Error ? err.message : "Unable to load provider summary");
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
    return <LoadingState label="Loading provider status" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (items.length === 0) {
    return <EmptyState title="No providers available" message="No provider records were returned." />;
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>Provider health</h2>
        <p>
          {dashboardDataMode === "live"
            ? "Live mode reads provider summaries from the backend and falls back to source-derived data only when needed."
            : "This page is currently backed by mock provider data."}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Provider inventory</h2>
            <p>Enabled status, fetch counts, valid counts, and the most recent error signal.</p>
          </div>
        </div>
        <ProviderTable items={items} />
      </section>
    </div>
  );
}
