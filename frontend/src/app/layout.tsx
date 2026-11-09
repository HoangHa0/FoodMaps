import type { Metadata } from "next";

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
  title: { default: "FoodMaps · Khám phá quán ngon quanh bạn", template: "%s · FoodMaps" },
  description: "Quyết định nên ăn ở đâu — một mình, theo lịch trình, hay cùng nhóm bạn.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" data-theme={ACTIVE_THEME} className="h-full antialiased">
      {/* VietMap GL JS is loaded by <VietMap /> itself, only on pages that show a map */}
      <body className="min-h-full flex flex-col">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}