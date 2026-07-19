import { redirect } from "next/navigation";

export default function LegacySourceDetailPage({
  params,
}: {
  params: { id: string };
}) {
  redirect(`/media/sources/${params.id}`);
}
