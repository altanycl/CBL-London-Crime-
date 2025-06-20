import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { FilterProvider } from "@/contexts/filter-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "London Crime Dashboard",
  description: "Dashboard for London crime data, statistics, and forecasting",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main className="min-h-screen bg-slate-100">
          <FilterProvider>
            {children}
          </FilterProvider>
        </main>
      </body>
    </html>
  );
} 