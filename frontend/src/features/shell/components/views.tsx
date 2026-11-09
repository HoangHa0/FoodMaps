"use client";

/** App shell views: sidebar, top bar, footer band, phone tab bar. Props in, markup out. */
import Link from "next/link";
import { type KeyboardEvent, type PointerEvent, type ReactNode, useRef } from "react";

import { IconCategories, IconGroup, IconHeart, IconMenu, IconPin, IconSearch, Logo, cn } from "@/ui";

import { type NavItem, SIDEBAR } from "../nav";

// --------------------------------------------------------------------------- sidebar

export interface CategoryLink {
  name: string;
  count: number;
  icon: string;
  href: string;
  active: boolean;
}

/**
 * Desktop sidebar. The ☰ button next to the logo (or Ctrl+B) folds it into an icon rail; its right
 * edge can be dragged to resize it, and dragging it very narrow folds it too.
 */
export function Sidebar({
  items,
  isActive,
  categories,
  collapsed,
  width,
  onToggle,
  onResize,
}: {
  items: NavItem[];
  isActive: (i: NavItem) => boolean;
  /** "Danh mục quán" block (rendered by the container: it reads the data and the URL). */
  categories: ReactNode;
  collapsed: boolean;
  width: number;
  onToggle: () => void;
  /** New expanded width in px, or "collapse" when dragged below the threshold. */
  onResize: (width: number | "collapse") => void;
}) {
  return (
    <aside
      id="app-sidebar"
      className="sticky top-0 hidden h-dvh shrink-0 bg-sunken lg:flex"
      style={{ width: collapsed ? SIDEBAR.collapsed : width }}
      aria-label="Thanh bên"
      data-collapsed={collapsed || undefined}
    >
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className={cn("flex h-18 shrink-0 items-center gap-2", collapsed ? "justify-center" : "pl-4 pr-3")}>
          <button
            type="button"
            onClick={onToggle}
            aria-controls="app-sidebar"
            aria-expanded={!collapsed}
            aria-label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
            title={`${collapsed ? "Mở rộng" : "Thu gọn"} thanh bên (Ctrl+B)`}
            className="inline-flex size-10 shrink-0 items-center justify-center rounded-full transition ease-standard hover:bg-surface/70"
          >
            <IconMenu className="size-5" aria-hidden />
          </button>
          {!collapsed && (
            <Link href="/" aria-label="FoodMaps: trang chủ" className="min-w-0 rounded-control">
              <Logo compact />
            </Link>
          )}
        </div>

        <nav className={cn("mt-2", collapsed ? "px-2" : "px-3")} aria-label="Điều hướng chính">
          <ul className="flex flex-col gap-0.5">
            {items.map((item) => (
              <li key={item.label}>
                <NavLink item={item} active={isActive(item)} collapsed={collapsed} />
              </li>
            ))}
          </ul>
        </nav>

        <hr className={cn("mt-4 border-border", collapsed ? "mx-3" : "mx-5")} />

        {categories}
      </div>

      <ResizeHandle collapsed={collapsed} width={width} onResize={onResize} onToggle={onToggle} />
    </aside>
  );
}

function ResizeHandle({
  collapsed,
  width,
  onResize,
  onToggle,
}: {
  collapsed: boolean;
  width: number;
  onResize: (width: number | "collapse") => void;
  onToggle: () => void;
}) {
  const start = useRef<{ x: number; w: number } | null>(null);

  function onPointerDown(e: PointerEvent<HTMLDivElement>) {
    start.current = { x: e.clientX, w: collapsed ? SIDEBAR.collapsed : width };
    e.currentTarget.setPointerCapture(e.pointerId);
    document.body.style.userSelect = "none";
  }
  function onPointerMove(e: PointerEvent<HTMLDivElement>) {
    if (!start.current) return;
    const next = start.current.w + e.clientX - start.current.x;
    onResize(next < SIDEBAR.collapseBelow ? "collapse" : Math.min(SIDEBAR.max, Math.max(SIDEBAR.min, next)));
  }
  function onPointerUp() {
    start.current = null;
    document.body.style.userSelect = "";
  }
  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const step = e.shiftKey ? 48 : 16;
    if (e.key === "ArrowLeft") onResize(collapsed || width - step < SIDEBAR.min ? "collapse" : width - step);
    else if (e.key === "ArrowRight") onResize(Math.min(SIDEBAR.max, (collapsed ? SIDEBAR.min : width) + step));
    else if (e.key === "Enter") onToggle();
    else return;
    e.preventDefault();
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Đổi độ rộng thanh bên"
      aria-valuemin={SIDEBAR.collapsed}
      aria-valuemax={SIDEBAR.max}
      aria-valuenow={collapsed ? SIDEBAR.collapsed : width}
      tabIndex={0}
      title="Kéo để đổi độ rộng · nhấn đúp để thu gọn / mở rộng"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onDoubleClick={onToggle}
      onKeyDown={onKeyDown}
      className="group relative w-2 shrink-0 cursor-col-resize touch-none outline-none"
    >
      <span
        className="absolute inset-y-0 right-0 w-px bg-border transition-all ease-standard group-hover:w-1 group-hover:bg-primary group-focus-visible:w-1 group-focus-visible:bg-primary group-active:bg-primary"
        aria-hidden
      />
    </div>
  );
}

function NavLink({ item, active, collapsed }: { item: NavItem; active: boolean; collapsed: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href ?? "/"}
      aria-current={active ? "page" : undefined}
      title={collapsed ? item.label : undefined}
      className={cn(
        "flex h-11 items-center gap-3.5 rounded-control text-sm transition ease-standard",
        collapsed ? "justify-center px-0" : "px-4",
        active ? "bg-surface/80 font-bold shadow-card" : "font-medium hover:bg-surface/50",
      )}
    >
      <Icon className={cn("size-5 shrink-0", active && "fill-primary")} aria-hidden strokeWidth={active ? 2.2 : 1.8} />
      <span className={cn("truncate", collapsed && "sr-only")}>{item.label}</span>
    </Link>
  );
}

/** "Danh mục quán": the real categories of the data, each one filters the home map. */
export function CategoryNav({
  categories,
  total,
  allHref,
  allActive,
  collapsed,
  loading,
}: {
  categories: CategoryLink[];
  total: number;
  allHref: string;
  allActive: boolean;
  collapsed: boolean;
  loading: boolean;
}) {
  const row = (active: boolean) =>
    cn(
      "flex h-10 w-full items-center gap-3 rounded-control text-sm transition ease-standard",
      collapsed ? "justify-center" : "px-2.5",
      active ? "bg-surface/80 font-bold shadow-card" : "hover:bg-surface/50",
    );
  return (
    <section className={cn("mt-4 flex min-h-0 flex-1 flex-col pb-4", collapsed ? "px-2" : "px-3")} aria-label="Danh mục quán">
      {!collapsed && (
        <h2 className="flex items-center gap-2.5 px-2.5 text-xs font-bold uppercase tracking-wide text-fg-muted">
          <IconCategories className="size-4" aria-hidden /> Danh mục quán
        </h2>
      )}
      <ul className="mt-2 flex min-h-0 flex-col gap-0.5 overflow-y-auto">
        <li>
          <Link href={allHref} className={row(allActive)} aria-current={allActive ? "page" : undefined} title={collapsed ? `Tất cả quán (${total})` : undefined}>
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-raised text-base" aria-hidden>
              🗺️
            </span>
            <span className={cn("flex-1 truncate text-left", collapsed && "sr-only")}>Tất cả quán</span>
            {!collapsed && <span className="text-xs tabular-nums text-fg-muted">{total}</span>}
          </Link>
        </li>
        {loading &&
          Array.from({ length: 4 }, (_, i) => (
            <li key={i} className={cn("flex h-10 items-center gap-3", collapsed ? "justify-center" : "px-2.5")} aria-hidden>
              <span className="size-8 animate-pulse rounded-full bg-surface/70" />
              {!collapsed && <span className="h-3 flex-1 animate-pulse rounded-control bg-surface/70" />}
            </li>
          ))}
        {categories.map((c) => (
          <li key={c.name}>
            <Link href={c.href} className={row(c.active)} aria-current={c.active ? "page" : undefined} title={collapsed ? `${c.name} (${c.count})` : undefined}>
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-raised text-base" aria-hidden>
                {c.icon}
              </span>
              <span className={cn("flex-1 truncate text-left", collapsed && "sr-only")}>{c.name}</span>
              {!collapsed && <span className="text-xs tabular-nums text-fg-muted">{c.count}</span>}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

// --------------------------------------------------------------------------- top bar

export function TopBar({
  search,
  userMenu,
  area,
}: {
  /** AI Match bar (desktop only; phones and tablets use the round button of the tab bar). */
  search: ReactNode;
  userMenu: ReactNode;
  /** Area the data covers (information, not a picker). */
  area: string;
}) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/60 bg-bg/90 px-4 backdrop-blur lg:static lg:h-auto lg:border-0 lg:bg-transparent lg:px-6 lg:pb-2 lg:pt-5 lg:backdrop-blur-none">
      <Link href="/" className="rounded-control lg:hidden" aria-label="FoodMaps: trang chủ">
        <Logo compact />
      </Link>
      <div className="flex min-w-0 flex-1 items-center">{search}</div>
      <span className="hidden shrink-0 items-center gap-1.5 text-sm text-fg-muted sm:inline-flex" title={`Dữ liệu quán hiện có ở ${area}`}>
        <IconPin className="size-4" aria-hidden />
        {area}
      </span>
      <div className="shrink-0">{userMenu}</div>
    </header>
  );
}

// --------------------------------------------------------------------------- footer band

const FEATURES = [
  { icon: IconSearch, title: "Tìm quán bằng AI", text: "Mô tả điều bạn muốn, FoodMaps chọn quán hợp nhất." },
  { icon: IconHeart, title: "Lưu và lên kế hoạch", text: "Giữ những quán muốn thử ở một nơi." },
  { icon: IconGroup, title: "Ăn cùng nhóm", text: "Tạo phòng, cả nhóm cùng bình chọn quán." },
];

export function FooterBand() {
  return (
    <footer className="relative mt-6 hidden overflow-hidden lg:block" aria-label="Giới thiệu FoodMaps">
      <svg viewBox="0 0 1290 40" preserveAspectRatio="none" className="block h-8 w-full" aria-hidden>
        <path d="M0 30 C200 18 380 20 600 28 C800 36 960 34 1080 16 C1160 6 1230 2 1290 6 V40 H0 Z" className="fill-band" />
      </svg>
      <div className="bg-band px-10 pb-6 pt-1">
        <ul className="grid max-w-5xl grid-cols-3">
          {FEATURES.map((f, i) => (
            <li key={f.title} className={cn("flex gap-3.5 px-6", i > 0 && "border-l border-fg/20")}>
              <f.icon className="mt-0.5 size-5.5 shrink-0" aria-hidden strokeWidth={1.8} />
              <div>
                <h3 className="text-sm font-bold">{f.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-fg-muted">{f.text}</p>
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-5 px-6 text-xs text-fg-muted">© {new Date().getFullYear()} FoodMaps · Dữ liệu quán do nhóm thu thập ở Hà Nội</p>
      </div>
    </footer>
  );
}

// --------------------------------------------------------------------------- phone tab bar

/**
 * Floating tab bar for phones and tablets: two destinations, the raised round AI search button in
 * the middle (the main action of the app, under the thumb), two destinations.
 */
export function MobileTabBar({
  items,
  isActive,
  onSearch,
}: {
  items: NavItem[];
  isActive: (i: NavItem) => boolean;
  onSearch: () => void;
}) {
  const enabled = items.filter((i) => i.href);
  const half = Math.ceil(enabled.length / 2);
  const tab = (item: NavItem) => {
    const active = isActive(item);
    const Icon = item.icon;
    return (
      <li key={item.label} className="flex-1">
        <Link
          href={item.href!}
          aria-current={active ? "page" : undefined}
          className={cn(
            "flex h-16 flex-col items-center justify-center gap-1 rounded-control text-xs transition ease-standard",
            active ? "font-bold text-fg" : "text-fg-muted hover:text-fg",
          )}
        >
          <Icon className={cn("size-5.5", active && "fill-primary")} aria-hidden strokeWidth={active ? 2.2 : 1.8} />
          {item.label}
        </Link>
      </li>
    );
  };
  return (
    <nav
      className="fixed inset-x-3 bottom-[calc(0.75rem+env(safe-area-inset-bottom))] z-30 mx-auto max-w-lg lg:hidden"
      aria-label="Điều hướng chính"
    >
      <ul className="flex items-center rounded-control border border-border bg-sunken/95 px-2 shadow-float backdrop-blur">
        {enabled.slice(0, half).map(tab)}
        <li className="flex w-20 shrink-0 justify-center">
          <button
            type="button"
            onClick={onSearch}
            aria-label="Tìm quán bằng AI"
            title="Tìm quán bằng AI"
            className="-mt-7 grid size-16 place-items-center rounded-full bg-surface-raised text-accent shadow-float ring-4 ring-bg transition ease-standard hover:scale-105 active:scale-95"
            data-testid="match-fab"
          >
            <IconSearch className="size-7" strokeWidth={2.6} aria-hidden />
          </button>
        </li>
        {enabled.slice(half).map(tab)}
      </ul>
    </nav>
  );
}
