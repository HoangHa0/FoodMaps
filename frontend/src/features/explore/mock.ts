/**
 * MOCK DATA for the Explore screen, copied from the UI design so the layout can be built and
 * reviewed before the real data exists. Everything here is replaced by real sources later:
 *   places, ratings, photos  -> M7 place summaries (GET /api/places/{id}/summary, live from Google)
 *   pins / map               -> M2 MapView (Google Maps JS); `mapPoint` disappears with it
 *   featured / dishes        -> M3 match results and M4 review analysis ("dishes to try")
 * Photos live in /public/mock and are placeholders cut from the mock-up.
 */

export interface PlaceTag {
  label: string;
}

export interface Dish {
  id: string;
  name: string;
  price: string;
  photo: string;
}

export interface ExplorePlace {
  id: string;
  name: string;
  subtitle: string;
  cuisine: string;
  rating: number;
  reviewCount: string; // already formatted ("1.2k", "982")
  distance: string; // already formatted ("0.4 mi")
  photo: string; // card photo
  heroPhoto: string; // large photo in the detail panel
  thumb: string; // small photo in the map preview card
  photoCount: number;
  tags: string[];
  description: string;
  openHours: string;
  payment: string;
  goodFor: string;
  dishes: Dish[];
  /** Pin position on the illustrated map, in % of the map image (0-100). Tip of the pin. */
  mapPoint: { x: number; y: number };
  pinTone: "highlight" | "neutral" | "hot";
  pinKind: "restaurant" | "cafe";
  featured: boolean;
  trending: boolean;
  openNow: boolean;
}

/** The illustration is 834 x 559 px; the mock-up placed pins in that pixel space. */
const IMG_W = 834;
const IMG_H = 559;
/** (cx, cy) = centre of the pin head in mock-up pixels, relative to the illustration. */
const mapPoint = (cx: number, cy: number) => ({ x: (cx / IMG_W) * 100, y: ((cy + 22) / IMG_H) * 100 });

const nakamuraDishes: Dish[] = [
  { id: "d1", name: "Tonkotsu Ramen", price: "$12", photo: "/mock/tonkotsu-ramen.jpg" },
  { id: "d2", name: "Spicy Miso Ramen", price: "$13", photo: "/mock/spicy-miso-ramen.jpg" },
  { id: "d3", name: "Gyoza (6 pcs)", price: "$8", photo: "/mock/gyoza.jpg" },
];

/** Filler values for background pins (places shown on the map but not in the featured row). */
const PLACE_DEFAULTS: Omit<ExplorePlace, "id" | "name" | "mapPoint" | "pinTone" | "pinKind"> = {
  subtitle: "Local favourite",
  cuisine: "Local",
  rating: 4.4,
  reviewCount: "210",
  distance: "0.9 mi",
  photo: "/mock/sakura-ramen.jpg",
  heroPhoto: "/mock/sakura-ramen.jpg",
  thumb: "/mock/sakura-ramen.jpg",
  photoCount: 3,
  tags: ["Local"],
  description: "A neighbourhood spot loved by locals.",
  openHours: "9:00 AM – 9:00 PM",
  payment: "Cash only",
  goodFor: "Quick bite",
  dishes: [],
  featured: false,
  trending: false,
  openNow: true,
};

function pinOnly(
  id: string,
  name: string,
  point: { x: number; y: number },
  pinTone: ExplorePlace["pinTone"],
  pinKind: ExplorePlace["pinKind"],
): ExplorePlace {
  return {
    ...PLACE_DEFAULTS,
    id,
    name,
    mapPoint: point,
    pinTone,
    pinKind,
  };
}

export const PLACES: ExplorePlace[] = [
  {
    id: "ramen-nakamura",
    name: "Ramen Nakamura",
    subtitle: "Authentic Japanese Ramen",
    cuisine: "Japanese",
    rating: 4.8,
    reviewCount: "1.2k",
    distance: "0.4 mi",
    photo: "/mock/ramen-nakamura-hero.jpg",
    heroPhoto: "/mock/ramen-nakamura-hero.jpg",
    thumb: "/mock/ramen-nakamura-thumb.jpg",
    photoCount: 8,
    tags: ["Ramen", "Cozy", "Local Favorite"],
    description:
      "A small, family-run shop serving rich, flavorful ramen with locally sourced ingredients. A true Kyoto classic.",
    openHours: "11:00 AM – 10:00 PM",
    payment: "Cash & Card",
    goodFor: "Family Friendly",
    dishes: nakamuraDishes,
    mapPoint: mapPoint(520, 343),
    pinTone: "highlight",
    pinKind: "restaurant",
    featured: false,
    trending: true,
    openNow: true,
  },
  {
    id: "sakura-ramen",
    name: "Sakura Ramen",
    subtitle: "Ramen & small plates",
    cuisine: "Japanese",
    rating: 4.7,
    reviewCount: "982",
    distance: "0.3 mi",
    photo: "/mock/sakura-ramen.jpg",
    heroPhoto: "/mock/sakura-ramen.jpg",
    thumb: "/mock/sakura-ramen.jpg",
    photoCount: 5,
    tags: ["Ramen", "Late night"],
    description: "Bright, busy ramen bar with a short menu and a long queue at lunch.",
    openHours: "10:30 AM – 11:00 PM",
    payment: "Card only",
    goodFor: "Quick bite",
    dishes: nakamuraDishes.slice(0, 2),
    mapPoint: mapPoint(273, 275),
    pinTone: "highlight",
    pinKind: "restaurant",
    featured: true,
    trending: true,
    openNow: true,
  },
  {
    id: "lantern-cafe",
    name: "The Lantern Café",
    subtitle: "Coffee & pastries",
    cuisine: "Café",
    rating: 4.6,
    reviewCount: "743",
    distance: "0.8 mi",
    photo: "/mock/lantern-cafe.jpg",
    heroPhoto: "/mock/lantern-cafe.jpg",
    thumb: "/mock/lantern-cafe.jpg",
    photoCount: 6,
    tags: ["Café", "Quiet", "Study spot"],
    description: "Warm lantern light, soft music and big tables: a calm place to read or work.",
    openHours: "7:00 AM – 9:00 PM",
    payment: "Cash & Card",
    goodFor: "Working",
    dishes: [],
    mapPoint: mapPoint(250, 340),
    pinTone: "neutral",
    pinKind: "cafe",
    featured: true,
    trending: false,
    openNow: true,
  },
  {
    id: "spice-route",
    name: "Spice Route",
    subtitle: "Modern Indian kitchen",
    cuisine: "Indian",
    rating: 4.8,
    reviewCount: "612",
    distance: "1.1 mi",
    photo: "/mock/spice-route.jpg",
    heroPhoto: "/mock/spice-route.jpg",
    thumb: "/mock/spice-route.jpg",
    photoCount: 4,
    tags: ["Spicy", "Groups"],
    description: "Sharing plates, tandoor grills and generous curries made for groups.",
    openHours: "5:00 PM – 11:00 PM",
    payment: "Cash & Card",
    goodFor: "Groups",
    dishes: [],
    mapPoint: mapPoint(407, 440),
    pinTone: "hot",
    pinKind: "restaurant",
    featured: true,
    trending: true,
    openNow: false,
  },
  {
    id: "maison-blanc",
    name: "Maison Blanc",
    subtitle: "French bistro",
    cuisine: "French",
    rating: 4.5,
    reviewCount: "421",
    distance: "1.4 mi",
    photo: "/mock/maison-blanc.jpg",
    heroPhoto: "/mock/maison-blanc.jpg",
    thumb: "/mock/maison-blanc.jpg",
    photoCount: 7,
    tags: ["Date night", "Wine"],
    description: "A bright little bistro with classic dishes and a friendly wine list.",
    openHours: "11:30 AM – 10:30 PM",
    payment: "Card only",
    goodFor: "Date night",
    dishes: [],
    mapPoint: mapPoint(740, 393),
    pinTone: "hot",
    pinKind: "restaurant",
    featured: true,
    trending: false,
    openNow: true,
  },
  // background pins: places on the map that are not in the featured row
  pinOnly("yellow-2", "Hidden gem", mapPoint(277, 422), "highlight", "restaurant"),
  pinOnly("coffee-2", "Corner coffee", mapPoint(486, 390), "neutral", "cafe"),
  pinOnly("cafe-red", "Tea house", mapPoint(81, 380), "hot", "cafe"),
  pinOnly("noodles", "Noodle stand", mapPoint(338, 497), "neutral", "restaurant"),
];



/** Hand-written district labels drawn on the illustration (positions in % of the image). */
export const MAP_LABELS = [
  { text: "Arashiyama", x: 4.2, y: 41.5, tilt: -8, arrow: true },
  { text: "Kiyomizu-dera", x: 71.8, y: 70.6, tilt: -9, arrow: true },
  { text: "Kamo River", x: 76, y: 92, tilt: -27, arrow: false },
];

export const EXPLORE_COPY = {
  headline: ["Discover", "Good Food,", "Near You"],
  subtitle: "Explore local eats, hidden gems and your next favorite meal.",
  note: ["Good food", "is always", "a good idea!"],
};

export const DEFAULT_PLACE_ID = "ramen-nakamura";
