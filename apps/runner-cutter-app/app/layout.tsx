import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import SideNav from "@/components/side-nav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Laser Runner Cutter",
  description: "Laser runner cutter control and automation",
};

// Disable scaling
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1.0,
  maximumScale: 1.0,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex h-screen overflow-hidden">
          <div className="flex-shrink-0 w-64 bg-gray-200 overflow-y-auto p-8">
            <SideNav />
          </div>
          <div className="flex-1 overflow-y-auto p-8">{children}</div>
        </div>
      </body>
    </html>
  );
}
