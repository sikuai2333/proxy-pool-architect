import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { PaginationControls } from "../components/common/PaginationControls";
import { MetricCard } from "../components/dashboard/MetricCard";
import { AsnDistributionTable } from "../components/geo/AsnDistributionTable";
import { CountryDistributionChart } from "../components/geo/CountryDistributionChart";
import { LatencyAnalysisPanel } from "../components/geo/LatencyAnalysisPanel";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { GeoSummary } from "../types";

const COUNTRY_PAGE_SIZE = 8;
const ASN_PAGE_SIZE = 10;
const GEO_INITIAL_LOAD_GUARD_MS = 5000;

export function GeoPage() {
  const { t, language, formatNumber } = useI18n();
  const [data, setData] = useState<GeoSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [countryPage, setCountryPage] = useState(1);
  const [asnPage, setAsnPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    let settled = false;
    const loadGuard = globalThis.setTimeout(() => {
      if (!cancelled && !settled) {
        setError(t("geo.loadError"));
        setLoading(false);
      }
    }, GEO_INITIAL_LOAD_GUARD_MS);

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
          settled = true;
          globalThis.clearTimeout(loadGuard);
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
      globalThis.clearTimeout(loadGuard);
    };
  }, [language]);

  useEffect(() => {
    if (!data) {
      return;
    }

    const maxCountryPage = Math.max(1, Math.ceil(data.countries.length / COUNTRY_PAGE_SIZE));
    const maxAsnPage = Math.max(1, Math.ceil(data.asns.length / ASN_PAGE_SIZE));
    if (countryPage > maxCountryPage) {
      setCountryPage(maxCountryPage);
    }
    if (asnPage > maxAsnPage) {
      setAsnPage(maxAsnPage);
    }
  }, [asnPage, countryPage, data]);

  if (loading) {
    return <LoadingState label={t("geo.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <ErrorState title={t("geo.emptyTitle")} message={t("geo.emptyMessage")} />;
  }

  const countryOffset = (countryPage - 1) * COUNTRY_PAGE_SIZE;
  const asnOffset = (asnPage - 1) * ASN_PAGE_SIZE;
  const countryItems = data.countries.slice(countryOffset, countryOffset + COUNTRY_PAGE_SIZE);
  const asnItems = data.asns.slice(asnOffset, asnOffset + ASN_PAGE_SIZE);
  const totalCountryPages = Math.max(1, Math.ceil(data.countries.length / COUNTRY_PAGE_SIZE));
  const totalAsnPages = Math.max(1, Math.ceil(data.asns.length / ASN_PAGE_SIZE));
  const geoStatusKey = data.coverage.geo_enabled ? "geo.backendGeoEnabled" : "geo.backendGeoDisabled";
  const geoFileKey = data.coverage.geo_file_exists ? "geo.fileAvailable" : "geo.fileMissing";

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("geo.coverage")}</h2>
        <p>{dashboardDataMode === "live" ? t("geo.liveNote") : t("geo.mockNote")}</p>
        <p>{t("geo.coverageHint", { status: t(geoStatusKey), file: t(geoFileKey) })}</p>
      </section>

      <section className="metric-section" aria-label={t("geo.coverage")}>
        <MetricCard
          label={t("geo.totalProxies")}
          value={formatNumber(data.coverage.total_proxies)}
          detail={t("geo.coverageDescription")}
        />
        <MetricCard
          label={t("geo.geoTagged")}
          value={formatNumber(data.coverage.geo_tagged_proxies)}
          detail={t("geo.coverageFile", { file: data.coverage.geo_file || t("common.notSet") })}
          tone="good"
        />
        <MetricCard
          label={t("geo.unresolved")}
          value={formatNumber(data.coverage.unresolved_proxies)}
          detail={t(geoFileKey)}
          tone={data.coverage.unresolved_proxies > 0 ? "warning" : "good"}
        />
        <MetricCard
          label={t("geo.geoStatus")}
          value={t(geoStatusKey)}
          detail={t(geoFileKey)}
          tone={data.coverage.geo_enabled ? "good" : "warning"}
        />
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("geo.countryDistribution")}</h2>
            <p>
              {countryItems.length === 0
                ? t("geo.emptyMessage")
                : t("common.listRange", {
                    start: formatNumber(countryOffset + 1),
                    end: formatNumber(countryOffset + countryItems.length),
                    total: formatNumber(data.countries.length)
                  })}
            </p>
          </div>
          <PaginationControls
            ariaLabel={t("geo.countryPaginationLabel")}
            page={countryPage}
            totalPages={totalCountryPages}
            disabled={loading || data.countries.length === 0}
            onPrevious={() => setCountryPage((current) => Math.max(1, current - 1))}
            onNext={() => setCountryPage((current) => Math.min(totalCountryPages, current + 1))}
          />
        </div>
        {countryItems.length === 0 ? (
          <EmptyState title={t("geo.emptyTitle")} message={t("geo.emptyMessage")} />
        ) : (
          <CountryDistributionChart items={countryItems} />
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("geo.asnDistribution")}</h2>
            <p>
              {asnItems.length === 0
                ? t("geo.emptyMessage")
                : t("common.listRange", {
                    start: formatNumber(asnOffset + 1),
                    end: formatNumber(asnOffset + asnItems.length),
                    total: formatNumber(data.asns.length)
                  })}
            </p>
          </div>
          <PaginationControls
            ariaLabel={t("geo.asnPaginationLabel")}
            page={asnPage}
            totalPages={totalAsnPages}
            disabled={loading || data.asns.length === 0}
            onPrevious={() => setAsnPage((current) => Math.max(1, current - 1))}
            onNext={() => setAsnPage((current) => Math.min(totalAsnPages, current + 1))}
          />
        </div>
        {asnItems.length === 0 ? (
          <EmptyState title={t("geo.emptyTitle")} message={t("geo.emptyMessage")} />
        ) : (
          <AsnDistributionTable items={asnItems} />
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("geo.latencyAnalysis")}</h2>
            <p>{t("geo.latencyDescription")}</p>
          </div>
        </div>
        <LatencyAnalysisPanel countries={data.countries} asns={data.asns} />
      </section>
    </div>
  );
}
