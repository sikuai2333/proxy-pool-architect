interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "neutral" | "good" | "warning" | "danger";
}

export function MetricCard({ label, value, detail, tone = "neutral" }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <p>{detail}</p> : null}
    </article>
  );
}
