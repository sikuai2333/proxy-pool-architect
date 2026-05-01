import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { AsnDistributionTable } from "../components/geo/AsnDistributionTable";
import { CountryDistributionChart } from "../components/geo/CountryDistributionChart";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { GeoSummary } from "../types";

export function GeoPage() {
  const { t } = useI18n();
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
          setError(err instanceof Error ? err.message : t("geo.loadError"));
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
    return <LoadingState label={t("geo.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data || (data.countries.length === 0 && data.asns.length === 0)) {
    return <EmptyState title={t("geo.emptyTitle")} message={t("geo.emptyMessage")} />;
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("geo.coverage")}</h2>
        <p>
          {dashboardDataMode === "live"
            ? t("geo.liveNote")
            : t("geo.mockNote")}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("geo.countryDistribution")}</h2>
            <p>{t("geo.countryDescription")}</p>
          </div>
        </div>
        <CountryDistributionChart items={data.countries.slice(0, 8)} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("geo.asnDistribution")}</h2>
            <p>{t("geo.asnDescription")}</p>
          </div>
        </div>
        <AsnDistributionTable items={data.asns.slice(0, 10)} />
      </section>
    </div>
  );
}
