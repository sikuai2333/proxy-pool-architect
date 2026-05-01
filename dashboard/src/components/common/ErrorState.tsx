import { useI18n } from "../../i18n";

interface ErrorStateProps {
  title?: string;
  message: string;
}

export function ErrorState({ title, message }: ErrorStateProps) {
  const { t } = useI18n();

  return (
    <div className="state state-error" role="alert">
      <strong>{title ?? t("common.unableToLoadData")}</strong>
      <p>{message}</p>
    </div>
  );
}
