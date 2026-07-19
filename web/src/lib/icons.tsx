import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Library,
  Settings,
  BarChart3,
  Home,
  Radio,
  Search,
  Telescope,
  Building2,
  Music,
  Landmark,
  RefreshCw,
  Plus,
  Link2,
  KeyRound,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  Lock,
  ChevronDown,
  Menu,
  Play,
  Globe,
  Heart,
  Target,
  Gavel,
  Download,
  MessageSquare,
  Moon,
  Sun,
} from "lucide-react";

/**
 * Single icon registry — pages/layout import names, not lucide packages.
 * Add new icons here when a second call site appears.
 */
export const icons = {
  dashboard: LayoutDashboard,
  library: Library,
  settings: Settings,
  chart: BarChart3,
  home: Home,
  radio: Radio,
  search: Search,
  telescope: Telescope,
  building: Building2,
  music: Music,
  landmark: Landmark,
  refresh: RefreshCw,
  plus: Plus,
  link: Link2,
  key: KeyRound,
  sparkles: Sparkles,
  alert: AlertCircle,
  check: CheckCircle2,
  arrowRight: ArrowRight,
  lock: Lock,
  chevronDown: ChevronDown,
  menu: Menu,
  play: Play,
  globe: Globe,
  heart: Heart,
  target: Target,
  gavel: Gavel,
  download: Download,
  message: MessageSquare,
  moon: Moon,
  sun: Sun,
} as const;

export type IconName = keyof typeof icons;

export function Icon({
  name,
  className,
}: {
  name: IconName;
  className?: string;
}) {
  const Comp: LucideIcon = icons[name];
  return <Comp className={className} aria-hidden />;
}
