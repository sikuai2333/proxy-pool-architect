import type { ReactNode } from "react";

import { useI18n } from "../../i18n";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "danger";
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: ReactNode;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  cancelLabel,
  tone = "default",
  pending = false,
  onConfirm,
  onCancel,
  children
}: ConfirmDialogProps) {
  const { t } = useI18n();

  if (!open) {
    return null;
  }

  const resolvedConfirmLabel = confirmLabel ?? t("common.confirm");
  const resolvedCancelLabel = cancelLabel ?? t("common.cancel");

  return (
    <div className="overlay" role="presentation">
      <div
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <div className="dialog-header">
          <h2 id="confirm-dialog-title">{title}</h2>
        </div>
        <p className="dialog-copy">{message}</p>
        {children}
        <div className="dialog-actions">
          <button className="button button-secondary" type="button" onClick={onCancel}>
            {resolvedCancelLabel}
          </button>
          <button
            className={tone === "danger" ? "button button-danger" : "button button-primary"}
            type="button"
            onClick={onConfirm}
            disabled={pending}
          >
            {pending ? t("common.working") : resolvedConfirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
