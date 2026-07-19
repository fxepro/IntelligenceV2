import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Media Intelligence",
  description: "v2 control plane — discover, process, and search media intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
