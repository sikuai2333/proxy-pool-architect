import { useEffect, useState } from "react";

import { ConfirmDialog } from "../components/common/ConfirmDialog";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { ProxyDetailDrawer } from "../components/proxies/ProxyDetailDrawer";
import { ProxyFilters, type ProxyFilterState } from "../components/proxies/ProxyFilters";
import { ProxyTable } from "../components/proxies/ProxyTable";
import { useI18n } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { ProxyEndpoint, ProxyFilterOptions, ProxyListResponse } from "../types";

const PAGE_SIZE = 8;

const defaultFilters: ProxyFilterState = {
  pool: "",
  scheme: "",
  anonymity: "",
  country: "",
  source: "",
  minScore: "",
  query: ""
};

const emptyOptions: ProxyFilterOptions = {
  countries: [],
  sources: []
};

function buildListMessage(
  response: ProxyListResponse | null,
  formatNumber: (value: number) => string,
  t: ReturnType<typeof useI18n>["t"]
) {
  if (!response) {
    return t("proxies.zeroCount");
  }

  if (response.total === 0) {
    return t("proxies.zeroCount");
  }

  const start = response.offset + 1;
  const end = response.offset + response.items.length;
  return t("proxies.listRange", {
    start: formatNumber(start),
    end: formatNumber(end),
    total: formatNumber(response.total)
  });
}

export function ProxiesPage() {
  const { t, formatNumber } = useI18n();
  const [filters, setFilters] = useState<ProxyFilterState>(defaultFilters);
  const [options, setOptions] = useState<ProxyFilterOptions>(emptyOptions);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ProxyListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedProxy, setSelectedProxy] = useState<ProxyEndpoint | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ProxyEndpoint | null>(null);
  const [deletePending, setDeletePending] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadOptions() {
      try {
        const nextOptions = await dashboardApi.getProxyFilterOptions();
        if (!cancelled) {
          setOptions(nextOptions);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("proxies.loadFilterError"));
        }
      }
    }

    void loadOptions();

    return () => {
      cancelled = true;
    };
  }, [t]);

  useEffect(() => {
    let cancelled = false;

    async function loadProxies() {
      setLoading(true);
      setError(null);

      try {
        const response = await dashboardApi.listProxies({
          pool: filters.pool || undefined,
          scheme: filters.scheme || undefined,
          anonymity: filters.anonymity || undefined,
          country: filters.country || undefined,
          source: filters.source || undefined,
          min_score: filters.minScore ? Number(filters.minScore) : undefined,
          q: filters.query.trim() || undefined,
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE
        });

        if (!cancelled) {
          if (response.items.length === 0 && response.total > 0 && page > 1) {
            setPage((current) => Math.max(1, current - 1));
            return;
          }

          setData(response);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t("proxies.loadListError"));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProxies();

    return () => {
      cancelled = true;
    };
  }, [filters, page, t]);

  async function openProxyDetails(proxy: ProxyEndpoint) {
    setDrawerOpen(true);
    setSelectedProxy(proxy);
    setDrawerLoading(true);

    try {
      const detail = await dashboardApi.getProxy(proxy.id);
      setSelectedProxy(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("proxies.loadDetailError"));
    } finally {
      setDrawerLoading(false);
    }
  }

  function closeDrawer() {
    setDrawerOpen(false);
    setSelectedProxy(null);
    setDrawerLoading(false);
  }

  function handleFilterChange(nextFilters: ProxyFilterState) {
    setFilters(nextFilters);
    setPage(1);
  }

  function resetFilters() {
    setFilters(defaultFilters);
    setPage(1);
  }

  async function confirmDelete() {
    if (!deleteTarget) {
      return;
    }

    setDeletePending(true);
    try {
      const result = await dashboardApi.deleteProxy(deleteTarget.id);
      if (!result.ok) {
        throw new Error(t("proxies.deleteMockFailure"));
      }

      if (selectedProxy?.id === deleteTarget.id) {
        closeDrawer();
      }

      const response = await dashboardApi.listProxies({
        pool: filters.pool || undefined,
        scheme: filters.scheme || undefined,
        anonymity: filters.anonymity || undefined,
        country: filters.country || undefined,
        source: filters.source || undefined,
        min_score: filters.minScore ? Number(filters.minScore) : undefined,
        q: filters.query.trim() || undefined,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE
      });

      if (response.items.length === 0 && response.total > 0 && page > 1) {
        setPage((current) => Math.max(1, current - 1));
      } else {
        setData(response);
      }

      setDeleteTarget(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("proxies.deleteError"));
    } finally {
      setDeletePending(false);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="proxies-page">
      <ProxyFilters value={filters} options={options} onChange={handleFilterChange} onReset={resetFilters} />

      <section className="panel panel-table" aria-label={t("proxies.inventory")}>
        <div className="panel-header">
          <div>
            <h2>{t("proxies.inventory")}</h2>
            <p>{buildListMessage(data, formatNumber, t)}</p>
          </div>
          <nav className="pagination" aria-label={t("proxies.paginationLabel")}>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1 || loading}
            >
              {t("proxies.paginationPrevious")}
            </button>
            <span>
              {t("proxies.paginationPage", { page, totalPages })}
            </span>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page >= totalPages || loading}
            >
              {t("proxies.paginationNext")}
            </button>
          </nav>
        </div>

        {loading ? <LoadingState label={t("proxies.loadingInventory")} /> : null}

        {!loading && error ? <ErrorState message={error} /> : null}

        {!loading && !error && data && data.items.length === 0 ? (
          <EmptyState
            title={t("proxies.emptyTitle")}
            message={t("proxies.emptyMessage")}
          />
        ) : null}

        {!loading && !error && data && data.items.length > 0 ? (
          <ProxyTable
            items={data.items}
            onView={(proxy) => {
              void openProxyDetails(proxy);
            }}
            onDelete={(proxy) => setDeleteTarget(proxy)}
          />
        ) : null}
      </section>

      <ProxyDetailDrawer
        open={drawerOpen}
        proxy={selectedProxy}
        loading={drawerLoading}
        onClose={closeDrawer}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        title={t("proxies.deleteTitle")}
        message={
          dashboardDataMode === "live"
            ? t("proxies.deleteLiveMessage")
            : t("proxies.deleteMockMessage")
        }
        confirmLabel={t("proxies.deleteConfirm")}
        tone="danger"
        pending={deletePending}
        onConfirm={() => {
          void confirmDelete();
        }}
        onCancel={() => setDeleteTarget(null)}
      >
        {deleteTarget ? (
          <div className="dialog-proxy">
            <strong>{deleteTarget.id}</strong>
            <span>{deleteTarget.source}</span>
          </div>
        ) : null}
      </ConfirmDialog>
    </div>
  );
}
