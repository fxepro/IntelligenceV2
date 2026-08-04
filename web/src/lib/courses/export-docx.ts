import { API_BASE } from "@/lib/api-base";

/** Download a course DOCX export; returns the saved filename. */
export async function downloadCourseDocx(courseId: string): Promise<string> {
  const res = await fetch(
    `${API_BASE}/api/v1/courses/courses/${encodeURIComponent(courseId)}/export.docx`,
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string" ? body.detail : `Export failed (${res.status})`,
    );
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const match = /filename="([^"]+)"/i.exec(cd);
  const filename = match?.[1] || `${courseId}.docx`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return filename;
}
