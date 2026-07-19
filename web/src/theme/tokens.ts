/**
 * Active brand theme for Intelligence (standard §15).
 * Light and dark palettes are independent — edit each mode separately.
 *
 * Brand kit:
 *   #345a78 slate primary
 *   #d8cec4 warm beige
 *   #7a2f44 wine / maroon
 *   #9a8a82 taupe
 *   #a8b6c4 cool blue-gray
 *   #0E171C text
 *   #8B9AA5 muted
 *   #2A343C border (dark)
 */

export const brand = {
  slate: "#345a78",
  beige: "#d8cec4",
  taupe: "#9a8a82",
  wine: "#7a2f44",
  coolGray: "#a8b6c4", // also CSS --cool / Tailwind `cool`
  text: "#0E171C",
  muted: "#8B9AA5",
  border: "#2A343C",
} as const;

export const theme = {
  id: "intelligence",
  name: "Intelligence",

  fonts: {
    display: ["var(--font-display)", "Jost", "system-ui", "sans-serif"],
    sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
    code: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
  },

  /** Core six + exceptions — sizes in rem; pages use token class names only. */
  fontSize: {
    h1: ["3rem", { lineHeight: "1.1", fontWeight: "700" }],
    h2: ["2.5rem", { lineHeight: "1.15", fontWeight: "700" }],
    h3: ["2rem", { lineHeight: "1.2", fontWeight: "700" }],
    h4: ["1.75rem", { lineHeight: "1.25", fontWeight: "600" }],
    h5: ["1.5rem", { lineHeight: "1.3", fontWeight: "600" }],
    body: ["1rem", { lineHeight: "1.7", fontWeight: "400" }],
    "display-xl": ["4.5rem", { lineHeight: "1.0", fontWeight: "700" }],
    "display-l": ["3.75rem", { lineHeight: "1.05", fontWeight: "700" }],
    h6: ["1.25rem", { lineHeight: "1.35", fontWeight: "600" }],
    "body-lg": ["1.125rem", { lineHeight: "1.7", fontWeight: "400" }],
    "body-sm": ["0.875rem", { lineHeight: "1.6", fontWeight: "400" }],
    caption: ["0.8125rem", { lineHeight: "1.5", fontWeight: "400" }],
    fine: ["0.75rem", { lineHeight: "1.5", fontWeight: "400" }],
  },

  container: {
    center: true,
    padding: "1.5rem",
    screens: {
      "2xl": "1350px",
    },
  },

  /** Chrome heights used by .page-main / shell min-heights */
  chrome: {
    dashboardTopbarRem: 4,
    marketingTopRem: 5,
  },

  radius: {
    lg: "var(--radius)",
    md: "calc(var(--radius) - 2px)",
    sm: "calc(var(--radius) - 4px)",
  },

  /** HSL channel triples — mirrored in globals.css; light ≠ dark roles. */
  colors: {
    light: {
      background: "30 20% 84%",
      foreground: "202 7% 8%",
      card: "30 28% 97%",
      primary: "207 40% 34%",
      secondary: "30 16% 78%",
      accent: "343 44% 33%",
      destructive: "343 50% 32%",
      muted: "30 14% 80%",
      "muted-foreground": "205 13% 38%",
      border: "20 12% 68%",
      ring: "207 40% 34%",
      radius: "0.625rem",
    },
    dark: {
      background: "202 12% 9%",
      foreground: "30 22% 90%",
      card: "343 42% 14%",
      primary: "210 22% 74%",
      secondary: "20 11% 56%",
      accent: "20 11% 56%",
      destructive: "343 46% 48%",
      muted: "343 42% 14%",
      "muted-foreground": "205 13% 62%",
      border: "210 8% 28%",
      ring: "20 11% 56%",
    },
  },

  brand,
} as const;

export type AppTheme = typeof theme;
