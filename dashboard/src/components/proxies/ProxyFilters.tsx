import type { ChangeEvent } from "react";

import { useI18n, type TranslationKey } from "../../i18n";
import type { ProxyAnonymity, ProxyFilterOptions, ProxyPool, ProxyScheme } from "../../types";

export interface ProxyFilterState {
  pool: "" | ProxyPool;
  scheme: "" | ProxyScheme;
  anonymity: "" | ProxyAnonymity;
  country: string;
  source: string;
  minScore: string;
  query: string;
}

interface ProxyFiltersProps {
  value: ProxyFilterState;
  options: ProxyFilterOptions;
  onChange: (next: ProxyFilterState) => void;
  onReset: () => void;
}

const pools: Array<"" | ProxyPool> = ["", "raw", "checked", "elite", "dead", "cooldown"];
const schemes: Array<"" | ProxyScheme> = ["", "http", "https", "socks4", "socks5"];
const anonymities: Array<"" | ProxyAnonymity> = ["", "unknown", "transparent", "anonymous", "elite"];

export function ProxyFilters({ value, options, onChange, onReset }: ProxyFiltersProps) {
  const { t } = useI18n();

  function updateField<Key extends keyof ProxyFilterState>(key: Key, nextValue: ProxyFilterState[Key]) {
    onChange(
      {
        ...value,
        [key]: nextValue
      } as ProxyFilterState
    );
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    const { name, value: nextValue } = event.target;
    if (name === "minScore") {
      updateField("minScore", nextValue);
      return;
    }

    if (name === "query") {
      updateField("query", nextValue);
    }
  }

  return (
    <section className="filter-panel" aria-label={t("proxies.filters")}>
      <div className="filter-grid">
        <label className="field">
          <span>{t("proxies.pool")}</span>
          <select value={value.pool} onChange={(event) => updateField("pool", event.target.value as ProxyFilterState["pool"])}>
            {pools.map((pool) => (
              <option key={pool || "all"} value={pool}>
                {pool ? t(`proxyPool.${pool}` as TranslationKey) : t("proxies.allPools")}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>{t("proxies.scheme")}</span>
          <select
            value={value.scheme}
            onChange={(event) => updateField("scheme", event.target.value as ProxyFilterState["scheme"])}
          >
            {schemes.map((scheme) => (
              <option key={scheme || "all"} value={scheme}>
                {scheme || t("proxies.allSchemes")}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>{t("proxies.anonymity")}</span>
          <select
            value={value.anonymity}
            onChange={(event) =>
              updateField("anonymity", event.target.value as ProxyFilterState["anonymity"])
            }
          >
            {anonymities.map((anonymity) => (
              <option key={anonymity || "all"} value={anonymity}>
                {anonymity ? t(`anonymity.${anonymity}` as TranslationKey) : t("proxies.allTypes")}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>{t("proxies.country")}</span>
          <select value={value.country} onChange={(event) => updateField("country", event.target.value)}>
            <option value="">{t("proxies.allCountries")}</option>
            {options.countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>{t("proxies.source")}</span>
          <select value={value.source} onChange={(event) => updateField("source", event.target.value)}>
            <option value="">{t("proxies.allSources")}</option>
            {options.sources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>{t("proxies.minScore")}</span>
          <input
            name="minScore"
            type="number"
            min="0"
            max="100"
            value={value.minScore}
            onChange={onInputChange}
            placeholder="0"
          />
        </label>

        <label className="field field-search">
          <span>{t("proxies.hostOrIp")}</span>
          <input
            name="query"
            type="search"
            value={value.query}
            onChange={onInputChange}
            placeholder={t("proxies.searchPlaceholder")}
          />
        </label>
      </div>

      <div className="filter-actions">
        <button className="button button-secondary" type="button" onClick={onReset}>
          {t("proxies.resetFilters")}
        </button>
      </div>
    </section>
  );
}
