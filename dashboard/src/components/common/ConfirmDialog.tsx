import type { ReactNode } from "react";

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
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "default",
  pending = false,
  onConfirm,
  onCancel,
  children
}: ConfirmDialogProps) {
  if (!open) {
    return null;
  }

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
            {cancelLabel}
          </button>
          <button
            className={tone === "danger" ? "button button-danger" : "button button-primary"}
            type="button"
            onClick={onConfirm}
            disabled={pending}
          >
            {pending ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
