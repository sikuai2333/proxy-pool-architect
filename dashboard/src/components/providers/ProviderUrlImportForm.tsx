import { useState, type FormEvent } from "react";

import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import { dashboardApi } from "../../lib/api-client";
import type { ProxyUrlImportFileType, ProxyUrlImportResult } from "../../types";

interface ProviderUrlImportFormProps {
  onImported: () => Promise<void>;
}

const fileTypeOptions: ProxyUrlImportFileType[] = ["auto", "http", "socks5", "all", "clash", "v2ray"];
const fileTypeLabels: Record<ProxyUrlImportFileType, TranslationKey> = {
  auto: "providers.fileType.auto",
  http: "providers.fileType.http",
  socks5: "providers.fileType.socks5",
  all: "providers.fileType.all",
  clash: "providers.fileType.clash",
  v2ray: "providers.fileType.v2ray"
};
const detectedFormatLabels: Record<ProxyUrlImportResult["detected_format"], TranslationKey> = {
  plain_text: "providers.detectedFormat.plain_text",
  clash_yaml: "providers.detectedFormat.clash_yaml",
  v2ray_uri_list: "providers.detectedFormat.v2ray_uri_list",
  base64_uri_list: "providers.detectedFormat.base64_uri_list"
};
const connectionModeLabels: Record<ProxyUrlImportResult["supported_connection_modes"][number], TranslationKey> = {
  direct: "providers.connectionMode.direct",
  core_adapter: "providers.connectionMode.core_adapter"
};

export function ProviderUrlImportForm({ onImported }: ProviderUrlImportFormProps) {
  const { formatNumber, t } = useI18n();
  const [url, setUrl] = useState("");
  const [fileType, setFileType] = useState<ProxyUrlImportFileType>("auto");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProxyUrlImportResult | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!url.trim()) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const next = await dashboardApi.importProxyUrl(url.trim(), fileType);
      setResult(next);
      await onImported();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("providers.importError"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{t("providers.importTitle")}</h2>
          <p>{t("providers.importDescription")}</p>
        </div>
      </div>

      <form className="import-form" onSubmit={(event) => void handleSubmit(event)}>
        <div className="import-grid">
          <label className="field field-search">
            <span>{t("providers.importUrl")}</span>
            <input
              type="url"
              inputMode="url"
              required
              autoComplete="off"
              placeholder={t("providers.importUrlPlaceholder")}
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
          </label>

          <label className="field">
            <span>{t("providers.importFileType")}</span>
            <select
              value={fileType}
              onChange={(event) => setFileType(event.target.value as ProxyUrlImportFileType)}
            >
              {fileTypeOptions.map((option) => (
                <option key={option} value={option}>
                  {t(fileTypeLabels[option])}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filter-actions">
          <div className="settings-status" aria-live="polite">
            {error ? <span className="status-text status-error">{error}</span> : null}
            {!error && result ? (
              <span className="status-text status-ok">
                {t("providers.importSuccess", { count: formatNumber(result.stored_count) })}
              </span>
            ) : null}
          </div>
          <button className="button button-primary" type="submit" disabled={submitting || !url.trim()}>
            {submitting ? t("common.working") : t("providers.importSubmit")}
          </button>
        </div>
      </form>

      {result ? (
        <div className="import-result-grid" aria-live="polite">
          <div>
            <span>{t("providers.importFetched")}</span>
            <strong>{formatNumber(result.fetched_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importValid")}</span>
            <strong>{formatNumber(result.valid_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importStored")}</span>
            <strong>{formatNumber(result.stored_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importDirect")}</span>
            <strong>{formatNumber(result.direct_supported_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importAdapter")}</span>
            <strong>{formatNumber(result.adapter_required_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importDuplicates")}</span>
            <strong>{formatNumber(result.duplicate_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importInvalid")}</span>
            <strong>{formatNumber(result.invalid_count)}</strong>
          </div>
          <div>
            <span>{t("providers.importUnsupported")}</span>
            <strong>{formatNumber(result.unsupported_count)}</strong>
          </div>
          <div className="import-result-wide">
            <span>{t("providers.importDetectedFormat")}</span>
            <strong>{t(detectedFormatLabels[result.detected_format])}</strong>
          </div>
          <div className="import-result-wide">
            <span>{t("providers.importProtocols")}</span>
            <strong>{result.detected_protocols.join(", ") || "-"}</strong>
          </div>
          <div className="import-result-wide">
            <span>{t("providers.importConnectionModes")}</span>
            <strong>
              {result.supported_connection_modes.map((mode) => t(connectionModeLabels[mode])).join(", ") || "-"}
            </strong>
          </div>
        </div>
      ) : null}

      {result?.adapter_required_count ? (
        <p className="import-adapter-hint">{t("providers.importAdapterHint")}</p>
      ) : null}
    </section>
  );
}
