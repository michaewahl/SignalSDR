import { getAllEntries } from "@/lib/data";
import CompetitorDetail from "./competitor-detail";

export function generateStaticParams() {
  return getAllEntries().map((c) => ({ id: c.id }));
}

export default async function CompetitorDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CompetitorDetail id={id} />;
}
