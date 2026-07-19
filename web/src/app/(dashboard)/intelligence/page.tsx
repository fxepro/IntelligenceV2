import { redirect } from "next/navigation";

/** Former Intelligence archive page — removed; Research is the entry under Intelligence. */
export default function LegacyIntelligencePage() {
  redirect("/research");
}
