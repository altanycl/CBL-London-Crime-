import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
<<<<<<< HEAD
=======
import { FilterProvider } from "@/contexts/filter-context";
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb

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
<<<<<<< HEAD
        <main className="min-h-screen bg-slate-100">{children}</main>
=======
        <main className="min-h-screen bg-slate-100">
          <FilterProvider>
            {children}
          </FilterProvider>
        </main>
>>>>>>> e780b3354e9a96e159021bfbaf01d17031f477eb
      </body>
    </html>
  );
} 