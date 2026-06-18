import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata = {
  title: "OptiGene — AI Portfolio Optimizer (Parallel Computing)",
  description: "Optimasi portofolio multi-aset menggunakan Genetic Algorithm yang dipercepat dengan PySpark & CUDA GPU.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="id" className={`${outfit.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans antialiased text-gray-100 bg-[#030712]">
        {children}
      </body>
    </html>
  );
}
