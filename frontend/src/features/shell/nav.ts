import { IconGroup, IconHeart, IconHome, IconTrips, type IconComponent } from "@/ui";

export interface NavItem {
  href: string | null; // null = not built yet (rendered disabled, "Sắp có")
  label: string;
  icon: IconComponent;
  /** Extra paths that also highlight this item (e.g. /group/ABC123 -> Nhóm). */
  match?: string[];
}

/** Main navigation (sidebar on desktop; tab bar on phones: two items, the search button, two items). */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Khám phá", icon: IconHome },
  { href: "/me", label: "Đã lưu", icon: IconHeart },
  { href: "/journey", label: "Chuyến đi", icon: IconTrips },
  { href: "/group", label: "Ăn nhóm", icon: IconGroup, match: ["/group/"] },
];

export function isActive(item: NavItem, pathname: string): boolean {
  if (!item.href) return false;
  if (item.href === "/") return pathname === "/";
  return pathname === item.href || pathname.startsWith(item.href + "/") || !!item.match?.some((m) => pathname.startsWith(m));
}

/** Desktop sidebar sizes in px: expanded width range, icon rail, drag-to-collapse threshold. */
export const SIDEBAR = { min: 216, max: 340, default: 248, collapsed: 76, collapseBelow: 160 } as const;
