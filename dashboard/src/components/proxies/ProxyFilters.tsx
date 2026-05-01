import type { ChangeEvent } from "react";

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
    <section className="filter-panel" aria-label="Proxy filters">
      <div className="filter-grid">
        <label className="field">
          <span>Pool</span>
          <select value={value.pool} onChange={(event) => updateField("pool", event.target.value as ProxyFilterState["pool"])}>
            {pools.map((pool) => (
              <option key={pool || "all"} value={pool}>
                {pool || "All pools"}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Scheme</span>
          <select
            value={value.scheme}
            onChange={(event) => updateField("scheme", event.target.value as ProxyFilterState["scheme"])}
          >
            {schemes.map((scheme) => (
              <option key={scheme || "all"} value={scheme}>
                {scheme || "All schemes"}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Anonymity</span>
          <select
            value={value.anonymity}
            onChange={(event) =>
              updateField("anonymity", event.target.value as ProxyFilterState["anonymity"])
            }
          >
            {anonymities.map((anonymity) => (
              <option key={anonymity || "all"} value={anonymity}>
                {anonymity || "All types"}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Country</span>
          <select value={value.country} onChange={(event) => updateField("country", event.target.value)}>
            <option value="">All countries</option>
            {options.countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Source</span>
          <select value={value.source} onChange={(event) => updateField("source", event.target.value)}>
            <option value="">All sources</option>
            {options.sources.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Minimum score</span>
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
          <span>Host or IP</span>
          <input
            name="query"
            type="search"
            value={value.query}
            onChange={onInputChange}
            placeholder="Search host or proxy id"
          />
        </label>
      </div>

      <div className="filter-actions">
        <button className="button button-secondary" type="button" onClick={onReset}>
          Reset filters
        </button>
      </div>
    </section>
  );
}
