import type { Metadata } from "next";
import Script from "next/script";

import "@fontsource/nunito-sans/400.css";
import "@fontsource/nunito-sans/600.css";
import "@fontsource/nunito-sans/700.css";
import "@fontsource/nunito-sans/800.css";
import "@fontsource/kalam/700.css";
import "@fontsource/caveat/500.css";
import "@fontsource/mali/600.css";
import "@fontsource/mali/700.css";

import { AppShell } from "@/features/shell";
import { ACTIVE_THEME } from "@/ui";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "FoodMaps",
  description: "Quyết định nên ăn ở đâu — một mình, theo lịch trình, hay cùng nhóm bạn.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" data-theme={ACTIVE_THEME} className="h-full antialiased">
      <head>
        {/* Nạp VietMap GL CSS */}
        <link
          rel="stylesheet"
          href="https://unpkg.com/@vietmap/vietmap-gl-js@6.0.1/dist/vietmap-gl.css"
        />
        {/* Nạp VietMap GL JS SDK */}
        <Script
          id="vietmap-gl-js"
          src="https://unpkg.com/@vietmap/vietmap-gl-js@6.0.1/dist/vietmap-gl.js"
          strategy="afterInteractive"
        />
      </head>
      <body className="min-h-full flex flex-col">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}