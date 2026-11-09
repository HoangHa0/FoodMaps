import { Suspense } from "react";

import { ExploreScreen } from "@/features/explore";

/**
 * Home = Explore. Route files only compose features and hold no logic.
 * ExploreScreen reads the URL (?loai=, ?quan=), which needs a Suspense boundary in the App Router.
 */
export default function HomePage() {
  return (
    <Suspense>
      <ExploreScreen />
    </Suspense>
  );
}
