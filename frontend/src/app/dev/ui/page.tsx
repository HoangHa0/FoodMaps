"use client";

import { useState } from "react";

import {
  Badge,
  BrushUnderline,
  Button,
  Card,
  Chip,
  HandNote,
  IconButton,
  IconHeart,
  IconTrending,
  Input,
  Logo,
  MapPin,
  Mascot,
  PopLines,
  ProgressBar,
  Rating,
  SearchInput,
  Sheet,
  Spinner,
} from "@/ui";

/**
 * UI kit: every primitive on one page. After a theme or design change, review /dev/ui first,
 * then the real screens. Adding a primitive = adding a section here.
 */
export default function UiKitPage() {
  const [sheet, setSheet] = useState(false);
  const [chip, setChip] = useState("Date");
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <h1 className="font-display text-2xl font-semibold">UI kit</h1>
      <Card className="flex flex-wrap items-center gap-3">
        <Button>Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="accent">✨ Tìm quán cho mình</Button>
        <Button variant="danger">Xoá</Button>
        <Button loading>Đang tải</Button>
        <Button size="sm">Nhỏ</Button>
        <Spinner />
      </Card>
      <Card className="flex flex-wrap gap-2">
        {["Date", "Học bài", "Đói bụng", "Dưới 100k", "Ăn khuya"].map((c) => (
          <Chip key={c} selected={chip === c} onClick={() => setChip(c)}>
            {c}
          </Chip>
        ))}
        <Badge tone="accent">92% MATCH</Badge>
        <Badge>yên tĩnh</Badge>
      </Card>
      <Card className="flex flex-col gap-3">
        <Input label="Tên đăng nhập" placeholder="ha_nguyen" hint="3-30 ký tự" />
        <Input label="Mật khẩu" type="password" error="Mật khẩu tối thiểu 8 ký tự" />
        <ProgressBar value={3} max={5} marker={3} label="Lượt thích" />
      </Card>
      <Card className="flex flex-wrap items-center gap-6">
        <Logo tagline="Good Food, Closer Than You Think." />
        <Logo compact />
        <Mascot className="w-24" />
        <Mascot variant="round" className="size-12" />
        <Mascot variant="flying" className="w-8" />
      </Card>
      <Card className="flex flex-wrap items-center gap-4">
        <MapPin tone="highlight" label="Featured place" />
        <MapPin tone="neutral" kind="cafe" label="Café" />
        <MapPin tone="hot" label="Trending restaurant" />
        <IconButton label="Save" icon={<IconHeart className="size-5" />} />
        <Rating value={4.8} count="1.2k reviews" />
        <Chip icon={<IconTrending className="size-4" />}>Trending</Chip>
      </Card>
      <Card className="flex flex-col gap-3">
        <SearchInput label="Search" placeholder="Search for cuisine, dish, or restaurant..." />
        <div className="flex items-center gap-4">
          <HandNote tilt={-10} className="text-2xl">Good food is always a good idea!</HandNote>
          <PopLines className="h-8 w-5" />
        </div>
        <BrushUnderline className="h-4 w-60" />
      </Card>
      <Button variant="secondary" onClick={() => setSheet(true)}>
        Mở bottom sheet
      </Button>
      <Sheet open={sheet} onClose={() => setSheet(false)} title="Bún chả Hàng Mành" modal>
        <p className="text-fg-muted">Nội dung sheet (kết quả Match / lobby / chi tiết quán).</p>
      </Sheet>
    </main>
  );
}
