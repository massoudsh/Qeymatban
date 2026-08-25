import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "قیمت‌بان | ارزش‌گذاری توضیح‌پذیر ملک",
  description: "بازه قیمت، فایل‌های مشابه و عوامل اثرگذار بر ارزش ملک",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
