import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { TopNav } from "@/components/layout/TopNav";
import { Footer } from "@/components/layout/Footer";
import { PremiumBackground } from "@/components/ui/PremiumBackground";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-heading",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HuntJob Pro | Inteligencia Artificial para tu Carrera",
  description: "Optimiza tu perfil, analiza el mercado y genera postulaciones hiper-personalizadas usando IA avanzada.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${plusJakartaSans.variable} ${spaceGrotesk.variable} font-sans h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col relative bg-transparent text-foreground">
        <PremiumBackground />
        <TopNav />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
