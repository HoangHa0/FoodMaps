import type { Metadata } from "next";

import { RoomScreen } from "@/features/group";

export async function generateMetadata({ params }: PageProps<"/group/[code]">): Promise<Metadata> {
  const { code } = await params;
  return { title: `Phòng ${code.toUpperCase()}` };
}

export default async function GroupRoomPage({ params }: PageProps<"/group/[code]">) {
  const { code } = await params;
  return <RoomScreen code={code.toUpperCase()} />;
}
