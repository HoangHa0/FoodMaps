import Link from "next/link";
  
import { AuthMenu } from "@/features/auth";
import { Card } from "@/ui";

/**
 * Home = map. Route files only compose features and hold no logic:
 *   <MapView />          from features/map
 *   <SearchBar />        from features/match
 *   <MatchResultSheet /> from features/match
 */
export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 p-6">
      <Card className="max-w-md">
        <h1 className="font-display text-2xl font-semibold">FoodMaps</h1>
        <p className="text-fg-muted">Placeholder home page. The map view (M2) will be mounted here.</p>
        <nav className="mt-4 flex flex-wrap items-center gap-3 text-sm underline">
          <AuthMenu />
          <Link href="/group">Group Session</Link>
          <Link href="/dev/ui">UI kit</Link>
        </nav>
      </Card>
    </main>
  );
}
