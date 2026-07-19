import { redirect } from "next/navigation";

/** Access credentials moved to Settings. */
export default function SourcesAccessRedirect() {
  redirect("/settings");
}
