import { RoomScreen } from "@/features/group";

export default async function GroupRoomPage({ params }: PageProps<"/group/[code]">) {
  const { code } = await params;
  return <RoomScreen code={code.toUpperCase()} />;
}
