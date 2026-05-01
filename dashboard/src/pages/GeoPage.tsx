import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { AsnDistributionTable } from "../components/geo/AsnDistributionTable";
import { CountryDistributionChart } from "../components/geo/CountryDistributionChart";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { GeoSummary } from "../types";

export function GeoPage() {
  const [data, setData] = useState<GeoSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const summary = await dashboardApi.getGeoSummary();
        if (!cancelled) {
          setData(summary);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load geo summary");
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
    return <LoadingState label="Loading geo summary" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data || (data.countries.length === 0 && data.asns.length === 0)) {
    return <EmptyState title="No geo data available" message="No country or ASN records were returned." />;
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>Geo coverage</h2>
        <p>
          {dashboardDataMode === "live"
            ? "Live mode reads geo summaries from the backend and can derive them from proxy snapshots when the endpoint is unavailable."
            : "This page is currently backed by mock operational data."}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Country distribution</h2>
            <p>Total proxies, elite count, and average latency by country.</p>
          </div>
        </div>
        <CountryDistributionChart items={data.countries.slice(0, 8)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>ASN distribution</h2>
            <p>Top ASN groups from the current pool.</p>
          </div>
        </div>
        <AsnDistributionTable items={data.asns.slice(0, 10)} />
      </section>
    </div>
  );
}
