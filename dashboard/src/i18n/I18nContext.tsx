import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { localeByLanguage, resources, type Language, type TranslationKey } from "./translations";

const STORAGE_KEY = "dashboard-language";

interface TranslationValues {
  [key: string]: string | number;
}

interface I18nContextValue {
  language: Language;
  locale: string;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey, values?: TranslationValues) => string;
  formatNumber: (value: number) => string;
  formatDateTime: (value?: string | null) => string;
  formatLatency: (value: number | null | undefined) => string;
  formatPercent: (value: number | null | undefined) => string;
  maskCredential: (value?: string | null) => string;
}

function isLanguage(value: string | null): value is Language {
  return value === "en" || value === "zh-CN";
}

function getInitialLanguage(): Language {
  const persisted = window.localStorage.getItem(STORAGE_KEY);
  if (isLanguage(persisted)) {
    return persisted;
  }

  return navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en";
}

function interpolate(template: string, values?: TranslationValues) {
  if (!values) {
    return template;
  }

  return template.replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) => {
    const value = values[key];
    return value === undefined ? match : String(value);
  });
}

const I18nContext = createContext<I18nContextValue | null>(null);

interface I18nProviderProps {
  children: ReactNode;
}

export function I18nProvider({ children }: I18nProviderProps) {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);
  const locale = localeByLanguage[language];

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo<I18nContextValue>(() => {
    const bundle = resources[language];

    function t(key: TranslationKey, values?: TranslationValues) {
      return interpolate(bundle[key], values);
    }

    function formatNumber(value: number) {
      return new Intl.NumberFormat(locale).format(value);
    }

    function formatDateTime(value?: string | null) {
      if (!value) {
        return t("common.unknown");
      }

      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return t("common.unknown");
      }

      return new Intl.DateTimeFormat(locale, {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      }).format(date);
    }

    function formatLatency(value: number | null | undefined) {
      return value == null ? t("common.unknown") : `${formatNumber(value)} ms`;
    }

    function formatPercent(value: number | null | undefined) {
      return value == null ? t("common.unknown") : `${Math.round(value * 100)}%`;
    }

    function maskCredential(value?: string | null) {
      if (!value) {
        return t("common.notSet");
      }

      if (value.length <= 2) {
        return "**";
      }

      return `${value.slice(0, 2)}***`;
    }

    return {
      language,
      locale,
      setLanguage,
      t,
      formatNumber,
      formatDateTime,
      formatLatency,
      formatPercent,
      maskCredential
    };
  }, [language, locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider");
  }

  return context;
}
