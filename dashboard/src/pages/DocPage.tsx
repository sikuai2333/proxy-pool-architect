import { useState } from "react";

import { MarkdownRenderer } from "../components/doc/MarkdownRenderer";
import { apiDocEn, apiDocZh } from "../docs/api-docs";
import { useI18n } from "../i18n";

type DocLang = "zh" | "en";

export function DocPage() {
  const { language } = useI18n();
  const [docLang, setDocLang] = useState<DocLang>(language === "zh-CN" ? "zh" : "en");

  const content = docLang === "zh" ? apiDocZh : apiDocEn;

  return (
    <div className="doc-page">
      <div className="doc-toolbar">
        <button
          className={`button button-secondary ${docLang === "zh" ? "doc-lang-active" : ""}`}
          type="button"
          onClick={() => setDocLang("zh")}
        >
          中文
        </button>
        <button
          className={`button button-secondary ${docLang === "en" ? "doc-lang-active" : ""}`}
          type="button"
          onClick={() => setDocLang("en")}
        >
          English
        </button>
      </div>
      <div className="doc-content">
        <MarkdownRenderer content={content} />
      </div>
    </div>
  );
}
