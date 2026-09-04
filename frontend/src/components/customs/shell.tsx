"use client";

/**
 * shell.tsx — the app shell: one route, five surfaces (overview, why it
 * exists, the paper, agent playground, merchant control room), the gate
 * diamond in the masthead, honest status chips, and a footer that says
 * the true things. Views swap instantly and settle in 300ms — no exit
 * lag, one motion system everywhere.
 */
import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Home, HelpCircle, FileText, Terminal, Settings } from "lucide-react";
import { LogoMark } from "./bits";
import { Landing } from "./landing";
import { WhyPage } from "./why";
import { PaperPage } from "./paper";
import { Playground } from "./playground";
import { ControlRoom } from "./control-room";
import { FloatingAgent } from "./floating-agent";
import { SystemThemeAsk } from "./theme";
import { SiteFooter } from "./footer";
import Dock from "./Dock";
import Shuffle from "./Shuffle";

export type View = "home" | "why" | "paper" | "agent" | "merchant";

const NAV = [
  { id: "home", label: "Overview", icon: Home },
  { id: "why", label: "Why", icon: HelpCircle },
  { id: "paper", label: "Paper", icon: FileText },
  { id: "agent", label: "Playground", icon: Terminal },
  { id: "merchant", label: "Control Room", icon: Settings },
] as const;

export function _projectXApp() {
  const [view, setView] = useState<View>("home");
  const [menuOpen, setMenuOpen] = useState(false);

  /** switch surface: instant swap + settle-in, back to the top of the page */
  const go = useCallback((v: View) => {
    setView(v);
    setMenuOpen(false);
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, []);

  /* the mobile menu: Escape closes it, like every other sheet on the desk */
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  return (
    <div className="flex min-h-screen flex-col">
      {/* ------------------------------ thin header ------------------------------ */}
      <div className="relative z-10 mx-auto flex w-full max-w-[1200px] items-center justify-between px-5 pt-5 sm:px-8">
        <button
          onClick={() => go("home")}
          className="group flex shrink-0 items-center gap-2.5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink"
          aria-label="_projectX home"
        >
          <LogoMark size={22} className="text-ink transition-transform duration-300 ease-[cubic-bezier(0.25,1,0.5,1)] group-hover:rotate-[-90deg]" />
          <Shuffle
            text="_PROJECTX"
            tag="span"
            textAlign="left"
            className="font-mono text-[17px] font-semibold tracking-[0.24em] text-ink"
            shuffleDirection="down"
            duration={0.3}
            shuffleTimes={2}
            stagger={0.035}
            scrambleCharset="PROJECTX01<>#/\\"
            colorFrom="var(--color-inksoft)"
            colorTo="var(--color-ink)"
            triggerOnHover
          />
        </button>
      </div>

      <Dock
        items={NAV.map((n) => ({
          icon: <n.icon strokeWidth={1.5} size={20} />,
          label: n.label,
          onClick: () => go(n.id),
          active: view === n.id,
        }))}
      />

      {/* ------------------------------ content ------------------------------ */}
      <main className="mx-auto w-full max-w-[1200px] flex-1 px-5 py-10 sm:px-8 sm:py-14">
        <div key={view} className="view-enter">
          {view === "home" && <Landing onEnter={go} />}
          {view === "why" && <WhyPage onEnter={go} />}
          {view === "paper" && <PaperPage onEnter={go} />}
          {view === "agent" && <Playground />}
          {view === "merchant" && <ControlRoom />}
        </div>
      </main>

      {/* ------------------------------ footer ------------------------------ */}
      <SiteFooter onEnter={go} />

      {/* the everywhere-agent — draggable, on every view, real shopping */}
      <FloatingAgent view={view} />
      <SystemThemeAsk />

    </div>
  );
}
