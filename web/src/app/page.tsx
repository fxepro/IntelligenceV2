
"use client";

import Link from "next/link";
import {
  Zap,
  Search,
  Youtube,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  PlayCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PlaceHolderImages } from "@/lib/placeholder-images";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { marketingNav } from "@/config/navigation";
import { ctas } from "@/config/ctas";

export default function LandingPage() {
  const heroImage = PlaceHolderImages.find((img) => img.id === "landing-hero");
  const featureImage1 = PlaceHolderImages.find((img) => img.id === "feature-transcribe");
  const featureImage2 = PlaceHolderImages.find((img) => img.id === "feature-ai");

  return (
    <div className="flex flex-col min-h-screen page-main bg-background text-foreground">
      <header className="fixed top-0 w-full z-50 glass border-b border-border/40 px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary rounded-lg">
            <Icon name="chart" className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-display font-bold text-body-lg tracking-tight">{site.shortName}</span>
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
        {/* Hero Section */}
        <section className="relative py-20 lg:py-32 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/10 blur-[120px] rounded-full -z-10" />
          <div className="container px-6 mx-auto grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-in slide-in-from-left duration-700">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-3 h-3" />
                Intelligence Platform
              </div>
              <h1 className="text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1]">
                Uncover the <span className="text-primary italic">DNA</span> of Viral Content.
              </h1>
              <p className="text-xl text-muted-foreground leading-relaxed max-w-xl">
                {site.name} automates discovery and ingestion across platforms, extracts high-fidelity
                transcripts, and turns video into searchable intelligence.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href="/dashboard">
                  <Button size="lg" className="rounded-full px-8 h-14 text-base font-bold gap-2">
                    Enter Dashboard <ArrowRight className="w-5 h-5" />
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="rounded-full px-8 h-14 text-base font-bold gap-2">
                  <PlayCircle className="w-5 h-5" /> Watch Demo
                </Button>
              </div>
              <div className="flex items-center gap-8 pt-4">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="w-10 h-10 rounded-full border-2 border-background bg-muted flex items-center justify-center text-[10px] font-bold">
                      OP{i}
                    </div>
                  ))}
                </div>
                <div className="text-sm text-muted-foreground">
                  <span className="font-bold text-foreground">500+</span> teams analyzing intelligence
                </div>
              </div>
            </div>

            <div className="relative animate-in slide-in-from-right duration-700">
              <div className="glass rounded-3xl overflow-hidden shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500">
                <img 
                  src={heroImage?.imageUrl} 
                  alt={heroImage?.description} 
                  data-ai-hint={heroImage?.imageHint}
                  className="w-full h-auto aspect-[4/3] object-cover" 
                />
              </div>
              <div className="absolute -bottom-6 -left-6 glass p-6 rounded-2xl shadow-xl animate-bounce">
                <Zap className="w-8 h-8 text-yellow-400 fill-current mb-2" />
                <div className="text-xs font-bold uppercase text-muted-foreground">Ingestion Speed</div>
                <div className="text-2xl font-bold">0.42s / video</div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 bg-muted/30">
          <div className="container px-6 mx-auto">
            <div className="text-center space-y-4 mb-16">
              <h2 className="text-3xl font-bold">Comprehensive Toolset</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto italic">Everything you need to gather, process, and analyze video intelligence at scale.</p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="pt-8 space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <Youtube className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">Bulk YouTube Ingest</h3>
                  <p className="text-muted-foreground text-sm">Submit channels, playlists, or search terms. We'll handle the scraping and queueing automatically.</p>
                </CardContent>
              </Card>
              <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="pt-8 space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
                    <Search className="w-6 h-6 text-accent-foreground" />
                  </div>
                  <h3 className="text-xl font-bold">Full-Text Search</h3>
                  <p className="text-muted-foreground text-sm">Index every word spoken in thousands of videos. Find exact mentions and patterns in seconds.</p>
                </CardContent>
              </Card>
              <Card className="border-none shadow-sm hover:shadow-md transition-shadow">
                <CardContent className="pt-8 space-y-4">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <ShieldCheck className="w-6 h-6 text-emerald-600" />
                  </div>
                  <h3 className="text-xl font-bold">Secure Exports</h3>
                  <p className="text-muted-foreground text-sm">Download processed data as CSV or JSON. Integrate {site.name} into your own local pipelines.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Feature Highlight */}
        <section className="py-24">
          <div className="container px-6 mx-auto grid lg:grid-cols-2 gap-20 items-center">
            <div className="order-2 lg:order-1">
              <img 
                src={featureImage1?.imageUrl} 
                alt={featureImage1?.description}
                data-ai-hint={featureImage1?.imageHint}
                className="rounded-3xl shadow-xl w-full h-auto" 
              />
            </div>
            <div className="space-y-6 order-1 lg:order-2">
              <h2 className="text-4xl font-bold leading-tight">AI-Powered Extraction</h2>
              <p className="text-lg text-muted-foreground italic">"The most accurate transcription engine I've used for short-form content."</p>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                  </div>
                  <p className="text-sm">High-fidelity transcription for 20+ languages.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                  </div>
                  <p className="text-sm">Automatic key topic and category tagging.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-1 w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                    <div className="w-2 h-2 rounded-full bg-primary" />
                  </div>
                  <p className="text-sm">Context-aware executive summaries.</p>
                </div>
              </div>
              <Button size="lg" variant="secondary" className="rounded-full">Learn More about Gemini Integration</Button>
            </div>
          </div>
        </section>
      </main>

      <footer className="py-12 border-t border-border/50 px-6">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2 grayscale opacity-50">
            <Icon name="chart" className="w-5 h-5" />
            <span className="font-display font-bold text-body-sm tracking-tight">{site.shortName}</span>
          </div>
          <div className="flex gap-8 text-body-sm text-muted-foreground">
            <Link href="#">Privacy Policy</Link>
            <Link href="#">Terms of Service</Link>
            <Link href="#">API Docs</Link>
          </div>
          <p className="text-fine text-muted-foreground uppercase tracking-widest font-bold">
            © {new Date().getFullYear()} {site.shortName}
          </p>
        </div>
      </footer>
    </div>
  );
}
