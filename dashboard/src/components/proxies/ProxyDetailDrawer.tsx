import { AnonymityBadge } from "./AnonymityBadge";
import { ProxyStatusBadge } from "./ProxyStatusBadge";
import { SchemeBadge } from "./SchemeBadge";
import { EmptyState } from "../common/EmptyState";
import { LoadingState } from "../common/LoadingState";
import { formatDateTime, formatLatency, maskCredential } from "../../lib/format";
import type { ProxyEndpoint } from "../../types";

interface ProxyDetailDrawerProps {
  open: boolean;
  proxy: ProxyEndpoint | null;
  loading: boolean;
  onClose: () => void;
}

export function ProxyDetailDrawer({ open, proxy, loading, onClose }: ProxyDetailDrawerProps) {
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
            <h2 id="proxy-detail-title">Proxy details</h2>
            <p>{proxy ? proxy.id : "Inspecting selected proxy"}</p>
          </div>
          <button className="button button-secondary" type="button" onClick={onClose}>
            Close
          </button>
        </div>

        {loading ? <LoadingState label="Loading proxy details" /> : null}

        {!loading && !proxy ? (
          <EmptyState title="No proxy selected" message="Pick a proxy row to inspect more detail." />
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
                <dt>Host</dt>
                <dd>{proxy.host}</dd>
              </div>
              <div>
                <dt>Port</dt>
                <dd>{proxy.port}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{proxy.source}</dd>
              </div>
              <div>
                <dt>Country</dt>
                <dd>{proxy.country || "Unknown"}</dd>
              </div>
              <div>
                <dt>ASN</dt>
                <dd>{proxy.asn || "Unknown"}</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{formatLatency(proxy.latency_ms)}</dd>
              </div>
              <div>
                <dt>Score</dt>
                <dd>{proxy.score}</dd>
              </div>
              <div>
                <dt>Success / fail</dt>
                <dd>
                  {proxy.success_count} / {proxy.fail_count}
                </dd>
              </div>
              <div>
                <dt>Last checked</dt>
                <dd>{formatDateTime(proxy.last_checked_at)}</dd>
              </div>
              <div>
                <dt>Last success</dt>
                <dd>{formatDateTime(proxy.last_success_at)}</dd>
              </div>
              <div>
                <dt>Authentication</dt>
                <dd>{proxy.auth_required ? "Configured and hidden" : "Not required"}</dd>
              </div>
              <div>
                <dt>Username</dt>
                <dd>
                  {proxy.username ? maskCredential(proxy.username) : proxy.auth_required ? "Hidden" : "Not set"}
                </dd>
              </div>
              <div>
                <dt>Password</dt>
                <dd>{proxy.auth_required ? "Configured and hidden" : "Not set"}</dd>
              </div>
              <div>
                <dt>Consecutive fail count</dt>
                <dd>{proxy.consecutive_fail_count ?? 0}</dd>
              </div>
              <div>
                <dt>Cooldown until</dt>
                <dd>{formatDateTime(proxy.cooldown_until)}</dd>
              </div>
            </dl>

            <div className="detail-error">
              <span>Last error</span>
              <p>{proxy.last_error || "No recent error"}</p>
            </div>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
