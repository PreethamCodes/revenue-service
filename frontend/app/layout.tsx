import type { Metadata } from "next";
import "./portal.css";
export const metadata: Metadata = {
  title: "Certificate register | Revenue Department",
  description:
    "Review income and caste certificates held by the Revenue Department.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
