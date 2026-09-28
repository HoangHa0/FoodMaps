/**
 * UI primitives. Features import visual building blocks ONLY from "@/ui".
 * The contract is each component's PROPS: internals (classes, libraries, animation) may change
 * freely during a redesign, but changing or removing props affects every feature.
 */
export { cn } from "./cn";
export { ACTIVE_THEME } from "./theme";
export { Badge } from "./primitives/Badge";
export { Button, type ButtonProps } from "./primitives/Button";
export { Card } from "./primitives/Card";
export { Chip, type ChipProps } from "./primitives/Chip";
export { Input, type InputProps } from "./primitives/Input";
export { ProgressBar } from "./primitives/ProgressBar";
export { Sheet } from "./primitives/Sheet";
export { Spinner } from "./primitives/Spinner";
