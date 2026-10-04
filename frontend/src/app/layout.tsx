import type { Metadata } from "next";

// Self-hosted fonts (@fontsource): no request to Google Fonts at runtime or build time.
// Each CSS file declares @font-face with unicode-range, so browsers download only the subsets
// a page actually uses (e.g. Mali's Vietnamese glyphs for headings with diacritics).
import "@fontsource/nunito-sans/400.css";
import "@fontsource/nunito-sans/600.css";
import "@fontsource/nunito-sans/700.css";
import "@fontsource/nunito-sans/800.css";
import "@fontsource/kalam/700.css";
import "@fontsource/caveat/500.css";
import "@fontsource/mali/600.css";
import "@fontsource/mali/700.css";

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
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
