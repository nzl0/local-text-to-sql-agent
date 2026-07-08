import { Check, AlertTriangle, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AutoFix, StageKey, StageState } from "@/types";

const STAGES: { key: StageKey; active: string; done: string }[] = [
  { key: "bulma", active: "İlgili tablolar bulunuyor", done: "İlgili tablolar bulundu" },
  { key: "uretim", active: "SQL üretiliyor", done: "SQL üretildi" },
  { key: "calistirma", active: "Sorgu çalıştırılıyor", done: "Sorgu çalıştırıldı" },
  { key: "yorumlama", active: "Sonuç yorumlanıyor", done: "Sonuç yorumlandı" },
];

interface StageTrackerProps {
  stages: Record<StageKey, StageState>;
  liveFixes: AutoFix[];
}

function Dot({ state }: { state: StageState }) {
  if (state === "tamam") {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand/90">
        <Check className="h-2.5 w-2.5 text-white" strokeWidth={3} />
      </span>
    );
  }
  if (state === "hata") {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-danger/90">
        <AlertTriangle className="h-2.5 w-2.5 text-white" strokeWidth={3} />
      </span>
    );
  }
  if (state === "calisiyor") {
    return (
      <span className="flex h-4 w-4 items-center justify-center">
        <span className="h-2.5 w-2.5 animate-pulse-dot rounded-full bg-brand shadow-brand-glow" />
      </span>
    );
  }
  // bekliyor
  return (
    <span className="flex h-4 w-4 items-center justify-center">
      <span className="h-2 w-2 rounded-full bg-white/15" />
    </span>
  );
}

export function StageTracker({ stages, liveFixes }: StageTrackerProps) {
  return (
    <div className="animate-fade-in rounded-xl border border-line-soft bg-raised p-4 shadow-card">
      <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-ink-muted">
        <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-brand" />
        Soru işleniyor
      </div>

      <ol className="space-y-2.5">
        {STAGES.map(({ key, active, done }) => {
          const state = stages[key];
          const label = state === "tamam" ? done : active;
          return (
            <li key={key} className="flex flex-col gap-1">
              <div
                className={cn(
                  "flex items-center gap-2.5 text-sm transition-colors duration-150",
                  state === "tamam" && "text-ink",
                  state === "calisiyor" && "text-ink",
                  state === "bekliyor" && "text-ink-faint",
                  state === "hata" && "text-danger"
                )}
              >
                <Dot state={state} />
                <span>
                  {label}
                  {state === "calisiyor" && <span className="text-ink-faint">…</span>}
                </span>
              </div>

              {/* Onarım notları yalnızca çalıştırma altında ve gerçekten olduysa (turuncu). */}
              {key === "calistirma" &&
                liveFixes.map((f) => (
                  <div
                    key={f.attempt}
                    className="ml-6 flex items-center gap-1.5 text-xs text-warn"
                  >
                    <Wrench className="h-3 w-3" />
                    {f.attempt}. deneme: hata alındı, SQL otomatik düzeltildi
                  </div>
                ))}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
