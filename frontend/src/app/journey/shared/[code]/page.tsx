import { SharedJourneyScreen } from "@/features/journey";

export const metadata = { title: "Lịch trình được chia sẻ" };

export default async function SharedJourneyPage({ params }: PageProps<"/journey/shared/[code]">) {
  const { code } = await params;
  return <SharedJourneyScreen code={code} />;
}
