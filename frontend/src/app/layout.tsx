import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "AI Chat Space",
  description: "A premium AI assistant environment with integrated web searches, stock queries, and GitHub MCP actions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${outfit.variable} h-full antialiased dark`}>
      <body className="h-full bg-[#070913] text-[#f3f4f6] font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
