import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DocGen AI",
  description: "Generate clean documentation from code using AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gradient-to-br from-slate-950 via-slate-900 to-black text-white min-h-screen">
        {children}
      </body>
    </html>
  );
}
