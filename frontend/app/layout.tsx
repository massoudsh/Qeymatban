import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "قیمت‌بان | اتاق ارزش‌گذاری",
  description: "پنل شفاف ارزش‌گذاری و پایش معاملات ملک",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
