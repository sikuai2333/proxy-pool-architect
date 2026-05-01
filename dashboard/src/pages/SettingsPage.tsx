import { useEffect, useState } from "react";

import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { languageLabels, languages, useI18n, type Language, type TranslationKey } from "../i18n";
import { dashboardApi, dashboardDataMode } from "../lib/api-client";
import type { DashboardSettings } from "../types";

function toNumber(value: string, fallback: number) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

export function SettingsPage() {
  const { language, setLanguage, t } = useI18n();
  const [settings, setSettings] = useState<DashboardSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messageKey, setMessageKey] = useState<TranslationKey | null>(null);

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
          setError(err instanceof Error ? err.message : t("settings.loadError"));
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
    return <LoadingState label={t("settings.loading")} />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!settings) {
    return <EmptyState title={t("settings.emptyTitle")} message={t("settings.emptyMessage")} />;
  }

  async function saveSettings() {
    if (!settings) {
      return;
    }

    setSaving(true);
    setError(null);
    setMessageKey(null);

    try {
      const saved = await dashboardApi.updateSettings(settings);
      setSettings(saved);
      setMessageKey("settings.saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("settings.saveError"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="section-page">
      <section className="panel panel-note">
        <h2>{t("settings.runtimeTitle")}</h2>
        <p>
          {dashboardDataMode === "live"
            ? t("settings.liveNote")
            : t("settings.mockNote")}
        </p>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("settings.preferences")}</h2>
            <p>{t("settings.preferencesDescription")}</p>
          </div>
        </div>

        <div className="settings-grid">
          <label className="field">
            <span>{t("settings.language")}</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
              {languages.map((item) => (
                <option key={item} value={item}>
                  {t(languageLabels[item])}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t("settings.schedulerTitle")}</h2>
            <p>{t("settings.schedulerDescription")}</p>
          </div>
        </div>

        <div className="settings-grid">
          <label className="field">
            <span>{t("settings.fetchInterval")}</span>
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
            <span>{t("settings.validationInterval")}</span>
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
            <span>{t("settings.validationTimeout")}</span>
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
            <span>{t("settings.validationConcurrency")}</span>
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
            <span>{t("settings.minimumEliteScore")}</span>
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
            <span>{t("settings.cooldownSeconds")}</span>
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
              <strong>{t("settings.authorizedTargets")}</strong>
              <p>{t("settings.authorizedTargetsDescription")}</p>
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
              <strong>{t("settings.blockPrivateNetworks")}</strong>
              <p>{t("settings.blockPrivateNetworksDescription")}</p>
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
              <strong>{t("settings.maskCredentials")}</strong>
              <p>{t("settings.maskCredentialsDescription")}</p>
            </div>
          </label>
        </div>

        <div className="filter-actions">
          <div className="settings-status">
            {messageKey ? <span className="status-text status-ok">{t(messageKey)}</span> : null}
            {!messageKey && dashboardDataMode === "live" ? (
              <span className="status-text status-unknown">{t("settings.connected")}</span>
            ) : null}
          </div>
          <button className="button button-primary" type="button" onClick={() => void saveSettings()} disabled={saving}>
            {saving ? t("settings.saving") : t("settings.save")}
          </button>
        </div>
      </section>
    </div>
  );
}
