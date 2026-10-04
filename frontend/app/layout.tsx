import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: { default: "Learning Space", template: "%s · Learning Space" },
  description: "Internal learning plans, progress and completion evidence.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
