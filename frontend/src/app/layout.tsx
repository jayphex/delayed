import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";


export const metadata: Metadata = {
  title: "nbadelayed",
  description: "Track delayed NBA games",
};
 
function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}

export default RootLayout;