interface ErrorStateProps {
  title?: string;
  message: string;
}

export function ErrorState({ title = "Unable to load data", message }: ErrorStateProps) {
  return (
    <div className="state state-error" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}
