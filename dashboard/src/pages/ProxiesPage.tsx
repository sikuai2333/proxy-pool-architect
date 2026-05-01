import { useEffect, useState } from "react";

import { ConfirmDialog } from "../components/common/ConfirmDialog";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { ProxyDetailDrawer } from "../components/proxies/ProxyDetailDrawer";
import { ProxyFilters, type ProxyFilterState } from "../components/proxies/ProxyFilters";
import { ProxyTable } from "../components/proxies/ProxyTable";
import { formatNumber } from "../lib/format";
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

function buildListMessage(response: ProxyListResponse | null) {
  if (!response) {
    return "0 proxies";
  }

  if (response.total === 0) {
    return "0 proxies";
  }

  const start = response.offset + 1;
  const end = response.offset + response.items.length;
  return `${formatNumber(start)}-${formatNumber(end)} of ${formatNumber(response.total)}`;
}

export function ProxiesPage() {
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
          setError(err instanceof Error ? err.message : "Unable to load filter options");
        }
      }
    }

    void loadOptions();

    return () => {
      cancelled = true;
    };
  }, []);

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
          setError(err instanceof Error ? err.message : "Unexpected proxy list error");
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
  }, [filters, page]);

  async function openProxyDetails(proxy: ProxyEndpoint) {
    setDrawerOpen(true);
    setSelectedProxy(proxy);
    setDrawerLoading(true);

    try {
      const detail = await dashboardApi.getProxy(proxy.id);
      setSelectedProxy(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load proxy detail");
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
        throw new Error("Mock delete did not remove the selected proxy");
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
      setError(err instanceof Error ? err.message : "Unable to delete the selected proxy");
    } finally {
      setDeletePending(false);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="proxies-page">
      <ProxyFilters value={filters} options={options} onChange={handleFilterChange} onReset={resetFilters} />

      <section className="panel panel-table" aria-label="Proxy inventory">
        <div className="panel-header">
          <div>
            <h2>Proxy inventory</h2>
            <p>{buildListMessage(data)}</p>
          </div>
          <div className="pagination">
            <button
              className="button button-secondary"
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page <= 1 || loading}
            >
              Previous
            </button>
            <span>
              Page {page} / {totalPages}
            </span>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page >= totalPages || loading}
            >
              Next
            </button>
          </div>
        </div>

        {loading ? <LoadingState label="Loading proxy inventory" /> : null}

        {!loading && error ? <ErrorState message={error} /> : null}

        {!loading && !error && data && data.items.length === 0 ? (
          <EmptyState
            title="No proxies matched the current filters"
            message="Adjust the filter set or clear the search to see more records."
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
        title="Delete proxy"
        message={
          dashboardDataMode === "live"
            ? "The selected proxy will be deleted through the backend API if the endpoint is available."
            : "The selected proxy will be removed from the in-memory mock dataset."
        }
        confirmLabel="Delete proxy"
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
