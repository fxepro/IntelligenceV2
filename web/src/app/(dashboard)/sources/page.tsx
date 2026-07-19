import { redirect } from "next/navigation";

/** Legacy path — Media sources live at /media/sources. */
export default function LegacySourcesPage() {
  redirect("/media/sources");
}
