import { EmptyState } from "../components/common/EmptyState";
import { useI18n } from "../i18n";

interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  const { t } = useI18n();

  return (
    <EmptyState
      title={t("placeholder.emptyTitle", { title })}
      message={t("placeholder.emptyMessage")}
    />
  );
}
