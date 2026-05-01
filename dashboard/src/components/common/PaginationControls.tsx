import { useI18n } from "../../i18n";

interface PaginationControlsProps {
  ariaLabel: string;
  page: number;
  totalPages: number;
  disabled?: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export function PaginationControls({
  ariaLabel,
  page,
  totalPages,
  disabled = false,
  onPrevious,
  onNext
}: PaginationControlsProps) {
  const { t } = useI18n();

  return (
    <nav className="pagination" aria-label={ariaLabel}>
      <button
        className="button button-secondary"
        type="button"
        onClick={onPrevious}
        disabled={disabled || page <= 1}
      >
        {t("common.paginationPrevious")}
      </button>
      <span>{t("common.paginationPage", { page, totalPages })}</span>
      <button
        className="button button-secondary"
        type="button"
        onClick={onNext}
        disabled={disabled || page >= totalPages}
      >
        {t("common.paginationNext")}
      </button>
    </nav>
  );
}
