"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { AuthMenu } from "@/features/auth";

import { isActive, NAV_ITEMS } from "../nav";
import { FooterBand, MobileTabBar, Sidebar, TopBar } from "./views";

/**
 * Frame around every page: sidebar (desktop) or top bar + tab bar (phone), top bar with search
 * and the user menu, decorative footer band. Pages render only their own content.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const active = (i: (typeof NAV_ITEMS)[number]) => isActive(i, pathname);
  return (
    <div className="flex min-h-dvh flex-1">
      <Sidebar items={NAV_ITEMS} isActive={active} />
      <div className="flex min-w-0 flex-1 flex-col pb-16 lg:pb-0">
        {/* MOCK: city + weather. TODO: user's city / a weather source */}
        <TopBar userMenu={<AuthMenu />} city="Kyoto" temperature="22°C" />
        <div className="flex flex-1 flex-col">{children}</div>
        <FooterBand />
      </div>
      <MobileTabBar items={NAV_ITEMS} isActive={active} />
    </div>
  );
}
