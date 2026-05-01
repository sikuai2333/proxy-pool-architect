import { describe, expect, it } from "vitest";

import { languageLabels, resources, type TranslationKey } from "./translations";

describe("dashboard translations", () => {
  it("keeps zh-CN resources complete with the English key set", () => {
    const englishKeys = Object.keys(resources.en) as TranslationKey[];
    const chineseKeys = Object.keys(resources["zh-CN"]);

    expect(chineseKeys).toHaveLength(englishKeys.length);
    englishKeys.forEach((key) => {
      expect(resources["zh-CN"][key]).toBeTruthy();
    });
  });

  it("includes settings language and navigation labels", () => {
    expect(languageLabels["zh-CN"]).toBe("language.zh-CN");
    expect(resources["zh-CN"]["settings.language"]).toBe("语言");
    expect(resources["zh-CN"]["nav.settings"]).toBe("设置");
  });
});
