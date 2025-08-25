import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PDF to Excel Converter",
  description: "Convert your PDF files to Excel spreadsheets with ease.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              console.log("--- JULES'S DEBUGGING SCRIPT ---");
              console.log("NEXT_PUBLIC_SUPABASE_URL:", "${process.env.NEXT_PUBLIC_SUPABASE_URL}");
              console.log("NEXT_PUBLIC_SUPABASE_ANON_KEY:", "${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}");
              console.log("NEXT_PUBLIC_BACKEND_URL:", "${process.env.NEXT_PUBLIC_BACKEND_URL}");
              console.log("--- END DEBUGGING SCRIPT ---");
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}