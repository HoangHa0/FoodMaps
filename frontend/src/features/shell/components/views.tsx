"use client";

/** App shell views: sidebar, top bar, footer band, phone tab bar. Props in, markup out. */
import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";

import {
  HandNote,
  IconChevronDown,
  IconCuisines,
  IconGroup,
  IconHeart,
  IconPin,
  IconSearch,
  IconSun,
  Logo,
  Mascot,
  PopLines,
  SearchInput,
  cn,
} from "@/ui";

import { type NavItem, POPULAR_CUISINES } from "../nav";

// --------------------------------------------------------------------------- sidebar

export function Sidebar({ items, isActive }: { items: NavItem[]; isActive: (i: NavItem) => boolean }) {
  return (
    <aside className="sticky top-0 hidden h-dvh w-61 shrink-0 flex-col overflow-hidden bg-sunken lg:flex" aria-label="Sidebar">
      <Link href="/" className="px-6 pt-8" aria-label="FoodMaps home">
        <Logo tagline="Good Food, Closer Than You Think." />
      </Link>

      <nav className="mt-9 px-5" aria-label="Main">
        <ul className="flex flex-col gap-0.5">
          {items.map((item) => (
            <li key={item.label}>
              <NavLink item={item} active={isActive(item)} />
            </li>
          ))}
        </ul>
      </nav>

      <hr className="mx-7 mt-5 border-border" />

      <section className="mt-5 px-7" aria-label="Popular cuisines">
        <h2 className="flex items-center gap-3 text-sm font-bold">
          <IconCuisines className="size-4.5" aria-hidden /> Popular Cuisines
        </h2>
        <ul className="mt-3 flex flex-col">
          {POPULAR_CUISINES.map((c) => (
            <li key={c.name}>
              {/* TODO(M3): link to a search filtered by this cuisine */}
              <button type="button" className="flex h-8.5 w-full items-center gap-3 rounded-control text-sm hover:bg-surface/50">
                <span className="relative size-7 shrink-0 overflow-hidden rounded-full ring-2 ring-surface-raised">
                  <Image src={c.photo} alt="" fill sizes="28px" className="object-cover" />
                </span>
                <span className="flex-1 text-left">{c.name}</span>
                <span className="tabular-nums">{c.count}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <div className="relative mt-auto h-48 shrink-0">
        <svg viewBox="0 0 245 120" preserveAspectRatio="none" className="absolute inset-x-0 bottom-0 h-30 w-full" aria-hidden>
          <path d="M0 20 C50 42 140 48 245 30 V120 H0 Z" className="fill-band" />
        </svg>
        <Mascot className="absolute bottom-26 left-4 w-22" />
        <PopLines className="absolute bottom-43 left-21 h-7 w-4 rotate-[-55deg]" />
        <HandNote tilt={-17} className="absolute bottom-33 left-30 text-xl leading-tight">
          Good food
          <br />
          leads to
          <br />
          great stories <IconHeart className="inline size-4" aria-hidden />
        </HandNote>
      </div>
    </aside>
  );
}

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  const body = (
    <>
      <Icon className={cn("size-5", active && "fill-fg")} aria-hidden strokeWidth={active ? 2.2 : 1.8} />
      {item.label}
    </>
  );
  const cls = cn(
    "flex h-11 items-center gap-4 rounded-control px-5 text-sm transition ease-standard",
    active ? "bg-surface/75 font-bold shadow-card" : "font-medium hover:bg-surface/45",
  );
  if (!item.href)
    return (
      <span className={cn(cls, "cursor-not-allowed opacity-80")} aria-disabled title="Coming soon">
        {body}
      </span>
    );
  return (
    <Link href={item.href} className={cls} aria-current={active ? "page" : undefined}>
      {body}
    </Link>
  );
}

// --------------------------------------------------------------------------- top bar

export function TopBar({ userMenu, city, temperature }: { userMenu: ReactNode; city: string; temperature: string }) {
  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 bg-bg/90 px-4 py-3 backdrop-blur lg:static lg:bg-transparent lg:pb-1.5 lg:pl-10 lg:pr-6 lg:pt-5 lg:backdrop-blur-none">
      <Link href="/" className="lg:hidden" aria-label="FoodMaps home">
        <Logo compact />
      </Link>
      {/* TODO(M3): replace with the semantic SearchBar (collapsed <-> overlay) */}
      <SearchInput
        label="Search for cuisine, dish, or restaurant"
        placeholder="Search for cuisine, dish, or restaurant..."
        className="hidden max-w-154 flex-1 md:flex"
      />
      <div className="ml-auto flex items-center gap-3">
        <button type="button" className="hidden h-10 items-center gap-2.5 rounded-control bg-surface px-5 text-sm font-semibold shadow-card sm:inline-flex">
          <IconPin className="size-4 fill-fg text-surface" aria-hidden />
          {city}
          <IconChevronDown className="size-4" aria-hidden />
        </button>
        <span className="hidden h-10 items-center gap-2 rounded-control bg-surface px-4 text-sm font-semibold shadow-card sm:inline-flex">
          <IconSun className="size-5 fill-primary text-primary" aria-hidden />
          {temperature}
        </span>
        <IconSearchMobile />
        <div className="ml-5">{userMenu}</div>
      </div>
    </header>
  );
}

function IconSearchMobile() {
  return (
    <button type="button" aria-label="Search" className="inline-flex size-10 items-center justify-center rounded-full bg-surface shadow-card md:hidden">
      <IconSearch className="size-4.5" aria-hidden />
    </button>
  );
}

// --------------------------------------------------------------------------- footer band

const FEATURES = [
  { icon: IconSearch, title: "Explore Nearby", text: "Find great food wherever you are." },
  { icon: IconHeart, title: "Save & Plan", text: "Keep your must-try spots in one place." },
  { icon: IconGroup, title: "Share & Connect", text: "See what others love and share your own." },
];

export function FooterBand() {
  return (
    <footer className="relative hidden overflow-hidden lg:block" aria-label="About FoodMaps">
      <svg viewBox="0 0 1290 60" preserveAspectRatio="none" className="-mt-6 block h-14 w-full" aria-hidden>
        <path d="M0 44 C200 30 380 32 600 42 C800 50 960 48 1080 26 C1160 10 1230 4 1290 10 V60 H0 Z" className="fill-band" />
      </svg>
      <div className="relative bg-band pb-5 pl-14 pr-80">
        <ul className="grid grid-cols-3">
          {FEATURES.map((f, i) => (
            <li key={f.title} className={cn("flex gap-4 px-6", i > 0 && "border-l border-fg/25")}>
              <f.icon className="mt-0.5 size-6 shrink-0" aria-hidden strokeWidth={1.8} />
              <div>
                <h3 className="text-sm font-bold">{f.title}</h3>
                <p className="mt-1 max-w-36 text-xs leading-relaxed text-fg-muted">{f.text}</p>
              </div>
            </li>
          ))}
        </ul>
        <HandNote tilt={-20} className="absolute bottom-10 right-50 text-xl">
          FoodMaps <IconHeart className="inline size-4" aria-hidden />
        </HandNote>
        <Mascot className="absolute -bottom-16 right-10 w-40" />
        <PopLines className="absolute bottom-16 right-50 h-6 w-4 rotate-[200deg]" />
        <PopLines className="absolute bottom-21 right-6 h-8 w-5 rotate-[-15deg]" flip />
      </div>
    </footer>
  );
}

// --------------------------------------------------------------------------- phone tab bar

export function MobileTabBar({ items, isActive }: { items: NavItem[]; isActive: (i: NavItem) => boolean }) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-sunken pb-[env(safe-area-inset-bottom)] lg:hidden" aria-label="Main">
      <ul className="grid grid-cols-4">
        {items
          .filter((i) => i.href)
          .map((item) => {
            const active = isActive(item);
            const Icon = item.icon;
            return (
              <li key={item.label}>
                <Link
                  href={item.href!}
                  aria-current={active ? "page" : undefined}
                  className={cn("flex flex-col items-center gap-0.5 py-2 text-xs", active ? "font-bold" : "text-fg-muted")}
                >
                  <Icon className={cn("size-5", active && "fill-primary text-fg")} aria-hidden />
                  {item.label}
                </Link>
              </li>
            );
          })}
      </ul>
    </nav>
  );
}
