"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { type ReactNode, Suspense, useMemo } from "react";

import { AuthMenu } from "@/features/auth";
import { CATEGORY_PARAM, categoryHref, countCategories, usePlaces } from "@/features/map";
import { MatchSearchBar, MatchSearchProvider, useOpenMatchSearch } from "@/features/match";

import { useSidebar } from "../hooks/useSidebar";
import { isActive, NAV_ITEMS } from "../nav";
import { CategoryNav, FooterBand, MobileTabBar, Sidebar, TopBar } from "./views";

/**
 * Frame around every page: sidebar (desktop) or top bar + floating tab bar (phones, tablets), the
 * AI search (top bar on desktop, round tab-bar button otherwise), footer band. Pages render only
 * their own content.
 */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <MatchSearchProvider>
      <Frame>{children}</Frame>
    </MatchSearchProvider>
  );
}

function Frame({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const active = (i: (typeof NAV_ITEMS)[number]) => isActive(i, pathname);
  const sidebar = useSidebar();
  const openSearch = useOpenMatchSearch();
  return (
    <div className="flex min-h-dvh flex-1">
      <a
        href="#main"
        className="sr-only z-50 rounded-control bg-fg px-4 py-2 font-semibold text-surface focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
      >
        Bỏ qua đến nội dung chính
      </a>
      <Sidebar
        items={NAV_ITEMS}
        isActive={active}
        collapsed={sidebar.collapsed}
        width={sidebar.width}
        onToggle={sidebar.toggle}
        onResize={sidebar.resize}
        categories={
          // useSearchParams needs a Suspense boundary; the fallback is the same list without the highlight
          <Suspense fallback={<SidebarCategories collapsed={sidebar.collapsed} activeCategory={null} />}>
            <SidebarCategoriesFromUrl collapsed={sidebar.collapsed} />
          </Suspense>
        }
      />
      {/* bottom padding: room for the floating tab bar on phones and tablets */}
      <div className="flex min-w-0 flex-1 flex-col pb-28 lg:pb-0">
        <TopBar search={<MatchSearchBar />} userMenu={<AuthMenu />} area="Hà Nội" />
        <div id="main" tabIndex={-1} className="flex flex-1 flex-col outline-none">
          {children}
        </div>
        <FooterBand />
      </div>
      <MobileTabBar items={NAV_ITEMS} isActive={active} onSearch={openSearch} />
    </div>
  );
}

function SidebarCategoriesFromUrl({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();
  const param = useSearchParams().get(CATEGORY_PARAM);
  return <SidebarCategories collapsed={collapsed} activeCategory={pathname === "/" ? param : null} />;
}

function SidebarCategories({ collapsed, activeCategory }: { collapsed: boolean; activeCategory: string | null }) {
  const pathname = usePathname();
  const places = usePlaces();
  const categories = useMemo(() => countCategories(places.data ?? []), [places.data]);
  return (
    <CategoryNav
      collapsed={collapsed}
      loading={places.isPending}
      total={places.data?.length ?? 0}
      allHref={categoryHref(null)}
      allActive={pathname === "/" && !activeCategory}
      categories={categories.map((c) => ({ ...c, href: categoryHref(c.name), active: c.name === activeCategory }))}
    />
  );
}
