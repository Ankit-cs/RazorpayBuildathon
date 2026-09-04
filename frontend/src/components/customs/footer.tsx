"use client";

/**
 * footer.tsx — the bottom of the desk, rebuilt on x.ai's footer pattern:
 * a left column (mark, one copyright line, the theme toggle and the
 * source pill at its foot) and quiet link columns on the right —
 * 13px links at half opacity that only reach full ink on approach.
 * No paragraphs, no stamps, no second bar. A footer says where things
 * are; it does not repeat the site.
 */
import { LogoMark } from "./bits";
import { ThemeToggle } from "./theme";
import type { View } from "./shell";

const GITHUB = "#";

const SITE: { label: string; view: View }[] = [
  { label: "Overview", view: "home" },
  { label: "Why it exists", view: "why" },
  { label: "The paper", view: "paper" },
  { label: "Playground", view: "agent" },
  { label: "Control room", view: "merchant" },
];

const EVIDENCE: [string, string][] = [
  ["JUDGE.md", `${GITHUB}/blob/main/JUDGE.md`],
  ["PAPER.md", `${GITHUB}/blob/main/PAPER.md`],
  ["llms.txt", `${GITHUB}/blob/main/llms.txt`],
  ["ENGINEERING_LOG.md", `${GITHUB}/blob/main/ENGINEERING_LOG.md`],
];

const COMMANDS: [string, string][] = [
  ["make triage", `${GITHUB}#triage`],
  ["make verify", `${GITHUB}#verify`],
  ["make fuzz", `${GITHUB}#fuzz`],
];

export function SiteFooter({ onEnter }: { onEnter: (view: View) => void }) {
  return (
    <footer className="mt-auto border-t border-line">
      <div className="mx-auto w-full max-w-[1200px] px-5 pb-12 pt-10 sm:px-8">
        <div className="flex flex-col gap-10 lg:flex-row lg:gap-16">
          {/* ---------------- the left column: mark, ©, lamp, source ---------------- */}
          <div className="flex shrink-0 flex-col lg:w-[260px]">
            <div>
              <button
                onClick={() => onEnter("home")}
                className="group flex items-center gap-2.5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink"
                aria-label="_projectX home"
              >
                <LogoMark
                  size={18}
                  className="text-ink/40 transition-colors group-hover:text-ink/70"
                />
                <span className="font-display text-[15px] font-semibold leading-none tracking-[-0.02em] text-ink/60 transition-colors group-hover:text-ink">
                  _projectX
                </span>
              </button>
              <p className="mt-5 text-[10px] leading-relaxed text-inksoft">
                © 2026 _projectX · Razorpay AI Buildathon 2026
                <br />
                Test mode only — no real money moves.
              </p>
            </div>

            <div className="mt-auto flex items-center gap-3 pt-8">

            </div>
          </div>

          {/* ---------------- quiet link columns ---------------- */}
          <nav className="flex flex-1 flex-wrap gap-x-14 gap-y-8" aria-label="footer">
            <div className="flex flex-col">
              <span className="mb-1.5 text-[13px] font-medium text-ink/70">Site</span>
              <div className="flex flex-col gap-1">
                {SITE.map((l) => (
                  <button
                    key={l.label}
                    onClick={() => onEnter(l.view)}
                    className="w-fit text-left text-[13px] leading-relaxed text-inksoft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col">
              <span className="mb-1.5 text-[13px] font-medium text-ink/70">Evidence</span>
              <div className="flex flex-col gap-1">
                {EVIDENCE.map(([label, href]) => (
                  <a
                    key={label}
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="w-fit font-mono text-[11.5px] leading-relaxed text-inksoft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                  >
                    {label}
                  </a>
                ))}
              </div>
            </div>

            <div className="flex flex-col">
              <span className="mb-1.5 text-[13px] font-medium text-ink/70">Verify</span>
              <div className="flex flex-col gap-1">
                {COMMANDS.map(([label, href]) => (
                  <a
                    key={label}
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="w-fit font-mono text-[11.5px] leading-relaxed text-inksoft transition-colors hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                  >
                    {label}
                  </a>
                ))}
              </div>
            </div>
          </nav>
        </div>
      </div>
    </footer>
  );
}
