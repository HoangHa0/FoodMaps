import type { Metadata } from "next";

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
