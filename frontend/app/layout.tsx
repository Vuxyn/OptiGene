import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-jakarta",
  display: "swap",
});

export const metadata: Metadata = {
  title: "OptiGene — Portfolio Optimizer",
  description:
    "Temukan alokasi investasi optimal dari data pasar nyata menggunakan Genetic Algorithm yang dipercepat PySpark & CUDA.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={`${plusJakarta.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans antialiased bg-[#0b0f1a] text-slate-100">
        {children}
      </body>
    </html>
  );
}
