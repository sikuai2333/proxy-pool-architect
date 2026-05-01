import { EmptyState } from "../components/common/EmptyState";

interface PlaceholderPageProps {
  title: string;
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <EmptyState
      title={`${title} has no data yet`}
      message="No records are available in this view."
    />
  );
}
