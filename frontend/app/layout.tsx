import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "قیمت‌بان | ارزش‌گذاری توضیح‌پذیر ملک",
  description: "داشبورد فیروزه‌ای قیمت‌بان برای ارزش‌گذاری داده‌محور املاک",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body className="vibefarsiTurquoise">{children}</body>
    </html>
  );
}
