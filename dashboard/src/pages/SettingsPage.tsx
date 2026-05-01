import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { DashboardSettings } from "../types";

function toNumber(value: string, fallback: number) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<DashboardSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const next = await dashboardApi.getSettings();
        if (!cancelled) {
          setSettings(next);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load settings");
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
    return <LoadingState label="Loading dashboard settings" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!settings) {
    return <EmptyState title="No settings available" message="No dashboard settings were returned." />;
  }

  async function saveSettings() {
    if (!settings) {
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const saved = await dashboardApi.updateSettings(settings);
      setSettings(saved);
      setMessage("Settings saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save settings");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>Runtime settings</h2>
        <p>
          {dashboardDataMode === "live"
            ? "Live mode reads and updates runtime-safe backend settings."
            : "This page is currently backed by mock settings data."}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Scheduler and validation</h2>
            <p>Only safe networking and quality-management settings are exposed here.</p>
          </div>
        </div>

        <div className="settings-grid">
          <label className="field">
            <span>Fetch interval seconds</span>
            <input
              type="number"
              min="60"
              value={settings.fetch_interval_seconds}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  fetch_interval_seconds: toNumber(event.target.value, settings.fetch_interval_seconds)
                })
              }
            />
          </label>

          <label className="field">
            <span>Validation interval seconds</span>
            <input
              type="number"
              min="60"
              value={settings.validate_interval_seconds}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  validate_interval_seconds: toNumber(event.target.value, settings.validate_interval_seconds)
                })
              }
            />
          </label>

          <label className="field">
            <span>Validation timeout seconds</span>
            <input
              type="number"
              min="1"
              value={settings.validate_timeout_seconds}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  validate_timeout_seconds: toNumber(event.target.value, settings.validate_timeout_seconds)
                })
              }
            />
          </label>

          <label className="field">
            <span>Validation concurrency</span>
            <input
              type="number"
              min="1"
              value={settings.validate_concurrency}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  validate_concurrency: toNumber(event.target.value, settings.validate_concurrency)
                })
              }
            />
          </label>

          <label className="field">
            <span>Minimum elite score</span>
            <input
              type="number"
              min="0"
              max="100"
              value={settings.min_elite_score}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  min_elite_score: toNumber(event.target.value, settings.min_elite_score)
                })
              }
            />
          </label>

          <label className="field">
            <span>Cooldown seconds</span>
            <input
              type="number"
              min="0"
              value={settings.cooldown_seconds}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  cooldown_seconds: toNumber(event.target.value, settings.cooldown_seconds)
                })
              }
            />
          </label>
        </div>

        <div className="settings-toggles">
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={settings.safe_networking.authorized_targets_only}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  safe_networking: {
                    ...settings.safe_networking,
                    authorized_targets_only: event.target.checked
                  }
                })
              }
            />
            <div>
              <strong>Authorized targets only</strong>
              <p>Keep dashboard-triggered networking limited to approved internal or owned targets.</p>
            </div>
          </label>

          <label className="toggle-row">
            <input
              type="checkbox"
              checked={settings.safe_networking.block_private_networks}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  safe_networking: {
                    ...settings.safe_networking,
                    block_private_networks: event.target.checked
                  }
                })
              }
            />
            <div>
              <strong>Block private networks</strong>
              <p>Avoid routing validation work into RFC1918 or local-only destinations by default.</p>
            </div>
          </label>

          <label className="toggle-row">
            <input
              type="checkbox"
              checked={settings.safe_networking.mask_proxy_credentials}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  safe_networking: {
                    ...settings.safe_networking,
                    mask_proxy_credentials: event.target.checked
                  }
                })
              }
            />
            <div>
              <strong>Mask proxy credentials</strong>
              <p>Never reveal proxy usernames or passwords in the dashboard UI.</p>
            </div>
          </label>
        </div>

        <div className="filter-actions">
          <div className="settings-status">
            {message ? <span className="status-text status-ok">{message}</span> : null}
            {!message && dashboardDataMode === "live" ? (
              <span className="status-text status-unknown">Connected to live settings API.</span>
            ) : null}
          </div>
          <button className="button button-primary" type="button" onClick={() => void saveSettings()} disabled={saving}>
            {saving ? "Saving..." : "Save settings"}
          </button>
        </div>
      </section>
    </div>
  );
}
