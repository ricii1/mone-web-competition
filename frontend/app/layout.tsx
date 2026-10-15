import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const display = localFont({
  src: "./fonts/baloo2-latin.woff2",
  weight: "400 800",
  display: "swap",
  variable: "--font-display",
});

const body = localFont({
  src: "./fonts/nunito-latin.woff2",
  weight: "200 1000",
  display: "swap",
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Peta Pintar",
  description: "Platform pembelajaran dengan peta level berbasis materi guru",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={`${display.variable} ${body.variable}`}>
      <body className="font-sans text-ink">{children}</body>
    </html>
  );
}
