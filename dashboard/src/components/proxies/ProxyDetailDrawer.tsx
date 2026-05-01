import { AnonymityBadge } from "./AnonymityBadge";
import { ProxyStatusBadge } from "./ProxyStatusBadge";
import { SchemeBadge } from "./SchemeBadge";
import { EmptyState } from "../common/EmptyState";
import { LoadingState } from "../common/LoadingState";
import { useI18n } from "../../i18n";
import type { ProxyEndpoint } from "../../types";

interface ProxyDetailDrawerProps {
  open: boolean;
  proxy: ProxyEndpoint | null;
  loading: boolean;
  onClose: () => void;
}

export function ProxyDetailDrawer({ open, proxy, loading, onClose }: ProxyDetailDrawerProps) {
  const { t, formatDateTime, formatLatency, maskCredential } = useI18n();

  if (!open) {
    return null;
  }

  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="proxy-detail-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-header">
          <div>
            <h2 id="proxy-detail-title">{t("proxies.detail.title")}</h2>
            <p>{proxy ? proxy.id : t("proxies.detail.inspecting")}</p>
          </div>
          <button className="button button-secondary" type="button" aria-label={t("common.close")} onClick={onClose}>
            {t("common.close")}
          </button>
        </div>

        {loading ? <LoadingState label={t("proxies.detail.loading")} /> : null}

        {!loading && !proxy ? (
          <EmptyState title={t("proxies.detail.emptyTitle")} message={t("proxies.detail.emptyMessage")} />
        ) : null}

        {!loading && proxy ? (
          <div className="drawer-body">
            <div className="drawer-badges">
              <ProxyStatusBadge status={proxy.status} />
              <SchemeBadge scheme={proxy.scheme} />
              <AnonymityBadge anonymity={proxy.anonymity} />
            </div>

            <dl className="detail-grid">
              <div>
                <dt>{t("proxies.table.host")}</dt>
                <dd>{proxy.host}</dd>
              </div>
              <div>
                <dt>{t("proxies.table.port")}</dt>
                <dd>{proxy.port}</dd>
              </div>
              <div>
                <dt>{t("proxies.table.source")}</dt>
                <dd>{proxy.source}</dd>
              </div>
              <div>
                <dt>{t("proxies.table.country")}</dt>
                <dd>{proxy.country || t("common.unknown")}</dd>
              </div>
              <div>
                <dt>ASN</dt>
                <dd>{proxy.asn || t("common.unknown")}</dd>
              </div>
              <div>
                <dt>{t("proxies.table.latency")}</dt>
                <dd>{formatLatency(proxy.latency_ms)}</dd>
              </div>
              <div>
                <dt>{t("proxies.table.score")}</dt>
                <dd>{proxy.score}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.successFail")}</dt>
                <dd>
                  {proxy.success_count} / {proxy.fail_count}
                </dd>
              </div>
              <div>
                <dt>{t("proxies.table.lastChecked")}</dt>
                <dd>{formatDateTime(proxy.last_checked_at)}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.lastSuccess")}</dt>
                <dd>{formatDateTime(proxy.last_success_at)}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.authentication")}</dt>
                <dd>{proxy.auth_required ? t("proxies.detail.authConfigured") : t("proxies.detail.authNotRequired")}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.username")}</dt>
                <dd>
                  {proxy.username ? maskCredential(proxy.username) : proxy.auth_required ? t("proxies.detail.hidden") : t("common.notSet")}
                </dd>
              </div>
              <div>
                <dt>{t("proxies.detail.password")}</dt>
                <dd>{proxy.auth_required ? t("proxies.detail.authConfigured") : t("common.notSet")}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.consecutiveFail")}</dt>
                <dd>{proxy.consecutive_fail_count ?? 0}</dd>
              </div>
              <div>
                <dt>{t("proxies.detail.cooldownUntil")}</dt>
                <dd>{formatDateTime(proxy.cooldown_until)}</dd>
              </div>
            </dl>

            <div className="detail-error">
              <span>{t("proxies.table.lastError")}</span>
              <p>{proxy.last_error || t("proxies.detail.noRecentError")}</p>
            </div>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
