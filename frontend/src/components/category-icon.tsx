import {
  BedDouble,
  Fuel,
  Globe,
  HeartPulse,
  Plane,
  Shirt,
  ShoppingCart,
  Smartphone,
  Sparkles,
  UtensilsCrossed,
  type LucideIcon,
} from "lucide-react";
import type { CategorySlug } from "@/lib/promotions";

const ICONS: Record<CategorySlug, LucideIcon> = {
  dining: UtensilsCrossed,
  supermarket: ShoppingCart,
  travel: Plane,
  hotels: BedDouble,
  fashion: Shirt,
  electronics: Smartphone,
  health: HeartPulse,
  fuel: Fuel,
  online: Globe,
  other: Sparkles,
};

export function CategoryIcon({ category, className }: { category: CategorySlug; className?: string }) {
  const Icon = ICONS[category];
  return <Icon className={className} aria-hidden />;
}
