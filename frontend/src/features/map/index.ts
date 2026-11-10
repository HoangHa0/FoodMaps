/** Public API of VietMap-backed map components. */
export { VietMap } from "./VietMap";
export { mapApi, type MapPlace } from "./api";
export { usePlaces } from "./hooks/usePlaces";
export {
  CATEGORY_PARAM,
  type CategoryCount,
  categoryHref,
  countCategories,
  normalizeCategory,
  PLACE_PARAM,
  placeHref,
} from "./lib/categories";
export { categoryIcon } from "./lib/categoryIcons";
