"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { marketingNav } from "@/config/navigation";
import { ctas } from "@/config/ctas";
import { DOMAINS } from "@/lib/domains";

/** Unsplash — Pinterest-home mix: travel, city, nature, food, culture, space. */
const COLLAGE = [
  {
    src: "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=640&q=70",
    alt: "Open road through desert mountains",
    className: "row-span-2 rotate-[-2deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=640&q=70",
    alt: "Mountain peaks above clouds",
    className: "rotate-[1.5deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=640&q=70",
    alt: "Prepared meal on a table",
    className: "rotate-[3deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1481627834876-b7833e8f5040?auto=format&fit=crop&w=640&q=70",
    alt: "Library shelves of books",
    className: "row-span-2 rotate-[-1.5deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?auto=format&fit=crop&w=640&q=70",
    alt: "City street at night",
    className: "rotate-[2deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=640&q=70",
    alt: "Earth from space",
    className: "row-span-2 rotate-[-3deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=640&q=70",
    alt: "Restaurant interior",
    className: "rotate-[1deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=640&q=70",
    alt: "Fog over forest hills",
    className: "rotate-[-2.5deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=640&q=70",
    alt: "Live music performance",
    className: "row-span-2 rotate-[2.5deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1541961017774-22349e4a1262?auto=format&fit=crop&w=640&q=70",
    alt: "Abstract painted canvas",
    className: "rotate-[-1deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=640&q=70",
    alt: "City skyline",
    className: "rotate-[3deg]",
  },
  {
    src: "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=640&q=70",
    alt: "Lake and mountains",
    className: "rotate-[-2deg]",
  },
] as const;

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen page-main bg-background text-foreground">
      <header className="fixed top-0 w-full z-50 glass border-b border-border/40 px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary rounded-lg">
            <Icon name="chart" className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-display font-bold text-body-lg tracking-tight">
            {site.shortName}
          </span>
        </div>
        <nav className="hidden md:flex items-center gap-8" aria-label="Marketing">
          {marketingNav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-body-sm font-medium hover:text-primary transition-colors"
            >
              {item.label}
            </Link>
          ))}
          <Link href={ctas.launchDashboard.href}>
            <Button variant="default" size="sm" className="rounded-full px-6">
              {ctas.launchDashboard.label}
            </Button>
          </Link>
        </nav>
      </header>

      <main className="flex-1 pt-16">
        {/* Hero — ~2× prior padding */}
        <section className="relative py-48 lg:py-64 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/10 blur-[120px] rounded-full -z-10" />
          <div className="container px-6 mx-auto max-w-4xl space-y-10 animate-in fade-in duration-700">
            <div className="space-y-6">
              <p className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight">
                {site.name}
              </p>
              <p className="text-xl sm:text-2xl text-muted-foreground leading-relaxed max-w-2xl">
                A worldwide intelligence platform covering all topics.
              </p>
            </div>
            <div>
              <Link href={ctas.launchDashboard.href}>
                <Button size="lg" className="rounded-full px-8 h-12 text-base font-bold">
                  {ctas.launchDashboard.label}
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Collage — ~half page+, Pinterest-style masonry */}
        <section
          id="features"
          className="relative min-h-[100vh] py-24 lg:py-32 border-y border-border/40 bg-muted/25 overflow-hidden"
          aria-label="Topics worldwide"
        >
          <div className="container px-4 sm:px-6 mx-auto max-w-6xl">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 auto-rows-[140px] sm:auto-rows-[180px] lg:auto-rows-[200px] gap-4 sm:gap-5">
              {COLLAGE.map((item) => (
                <figure
                  key={item.src}
                  className={`relative overflow-hidden rounded-2xl shadow-md bg-muted ${item.className}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.src}
                    alt={item.alt}
                    loading="lazy"
                    decoding="async"
                    className="absolute inset-0 h-full w-full object-cover"
                  />
                </figure>
              ))}
            </div>
          </div>
        </section>

        {/* Domains — 2× vertical space */}
        <section id="domains" className="py-48 lg:py-64">
          <div className="container px-6 mx-auto max-w-4xl space-y-10">
            <h2 className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
              Domains
            </h2>
            <ul className="flex flex-wrap gap-x-6 gap-y-4">
              {DOMAINS.map((d) => (
                <li key={d.key}>
                  <span
                    className={
                      d.enabled
                        ? "text-base font-medium text-foreground"
                        : "text-base text-muted-foreground/55"
                    }
                  >
                    {d.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section id="how-it-works" className="pb-48 lg:pb-64">
          <div className="container px-6 mx-auto max-w-4xl">
            <p className="text-[48px] leading-tight text-muted-foreground max-w-3xl tracking-tight">
              One platform. Topics worldwide. Sources in, intelligence out.
            </p>
          </div>
        </section>
      </main>

      <footer className="py-12 border-t border-border/50 px-6">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2 grayscale opacity-50">
            <Icon name="chart" className="w-5 h-5" />
            <span className="font-display font-bold text-body-sm tracking-tight">
              {site.shortName}
            </span>
          </div>
          <p className="text-fine text-muted-foreground uppercase tracking-widest font-bold">
            © {new Date().getFullYear()} {site.shortName}
          </p>
        </div>
      </footer>
    </div>
  );
}
