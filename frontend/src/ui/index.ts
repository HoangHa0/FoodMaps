/**
 * UI primitives. Features import visual building blocks ONLY from "@/ui".
 * The contract is each component's PROPS: internals (classes, libraries, animation) may change
 * freely during a redesign, but changing or removing props affects every feature.
 */
export { cn } from "./cn";
export * from "./icons";
export { ACTIVE_THEME } from "./theme";
export { Badge } from "./primitives/Badge";
export { Button, type ButtonProps } from "./primitives/Button";
export { Card } from "./primitives/Card";
export { Chip, type ChipProps } from "./primitives/Chip";
export { BrushUnderline, HandNote, PopLines } from "./primitives/HandNote";
export { IconButton, type IconButtonProps } from "./primitives/IconButton";
export { Input, type InputProps } from "./primitives/Input";
export { Logo } from "./primitives/Logo";
export { MapPin } from "./primitives/MapPin";
export { Mascot } from "./primitives/Mascot";
export { ProgressBar } from "./primitives/ProgressBar";
export { Rating } from "./primitives/Rating";
export { SearchInput, type SearchInputProps } from "./primitives/SearchInput";
export { Sheet } from "./primitives/Sheet";
export { Spinner } from "./primitives/Spinner";
