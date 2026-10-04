import { IconGroup, IconHeart, IconHome, IconSettings, IconTrips, type IconComponent } from "@/ui";

export interface NavItem {
  href: string | null; // null = not built yet (rendered disabled)
  label: string;
  icon: IconComponent;
  /** Extra paths that also highlight this item (e.g. /group/ABC123 -> Community). */
  match?: string[];
}

/** Main navigation. Labels follow the UI design; routes are the existing app routes. */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Explore", icon: IconHome },
  { href: "/me", label: "Saved", icon: IconHeart },
  { href: "/journey", label: "My Trips", icon: IconTrips },
  { href: "/group", label: "Community", icon: IconGroup, match: ["/group/"] },
  { href: null, label: "Settings", icon: IconSettings },
];

export function isActive(item: NavItem, pathname: string): boolean {
  if (!item.href) return false;
  if (item.href === "/") return pathname === "/";
  return pathname === item.href || pathname.startsWith(item.href + "/") || !!item.match?.some((m) => pathname.startsWith(m));
}

/** MOCK: cuisine counts for the sidebar. TODO(M2/M3): counts from the places table. */
export const POPULAR_CUISINES = [
  { name: "Japanese", count: 124, photo: "/mock/cuisine-japanese.jpg" },
  { name: "Italian", count: 98, photo: "/mock/cuisine-italian.jpg" },
  { name: "Thai", count: 87, photo: "/mock/cuisine-thai.jpg" },
  { name: "Mexican", count: 72, photo: "/mock/cuisine-mexican.jpg" },
  { name: "Indian", count: 64, photo: "/mock/cuisine-indian.jpg" },
  { name: "Korean", count: 53, photo: "/mock/cuisine-korean.jpg" },
  { name: "French", count: 38, photo: "/mock/cuisine-french.jpg" },
  { name: "American", count: 31, photo: "/mock/cuisine-american.jpg" },
  { name: "Chinese", count: 28, photo: "/mock/cuisine-chinese.jpg" },
];
