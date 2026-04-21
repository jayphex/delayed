import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Delayed",
  description: "Track how late NBA games tip compared to their scheduled start time.",
};

function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

export default RootLayout;
