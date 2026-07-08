import { History, CircleCheck, CircleSlash, CircleAlert, Loader2, ArrowRight, Inbox } from "lucide-react";
import { ViewShell } from "./ViewShell";
import { cn } from "@/lib/utils";
import type { Entry, EntryStatus } from "@/types";

const STATUS: Record<EntryStatus, { label: string; icon: typeof CircleCheck; cls: string }> = {
  success: { label: "Sonuç bulundu", icon: CircleCheck, cls: "text-ok" },
  empty: { label: "Kayıt yok", icon: CircleSlash, cls: "text-ink-muted" },
  error: { label: "Hata", icon: CircleAlert, cls: "text-danger" },
  processing: { label: "İşleniyor", icon: Loader2, cls: "text-brand" },
};

interface HistoryViewProps {
  entries: Entry[];
  onOpen: (id: number) => void;
}

// Geçmiş Analizler: oturum içi gerçek soru-cevap kayıtları. Tıklanınca Ana
// Sayfa'da ilgili karta gider.
export function HistoryView({ entries, onOpen }: HistoryViewProps) {
  return (
    <ViewShell
      title="Geçmiş Analizler"
      description="Bu oturumda çalıştırılan sorgular. (Sayfa yenilenince sıfırlanır.)"
      icon={<History className="h-5 w-5" />}
    >
      {entries.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-line-soft bg-surface py-12 text-center">
          <Inbox className="h-6 w-6 text-ink-faint" />
          <p className="text-sm text-ink-muted">Henüz analiz yok. Ana Sayfa'dan bir soru sorun.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {[...entries].reverse().map((e) => {
            const s = STATUS[e.status];
            const rows = e.result?.rows?.length ?? 0;
            return (
              <li key={e.id}>
                <button
                  type="button"
                  onClick={() => onOpen(e.id)}
                  className="group flex w-full items-center gap-3 rounded-lg border border-line-soft bg-surface px-4 py-3 text-left transition-all duration-150 hover:border-brand/50 hover:bg-hover"
                >
                  <s.icon className={cn("h-4 w-4 shrink-0", s.cls, e.status === "processing" && "animate-spin")} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm text-ink">{e.question}</div>
                    <div className="mt-0.5 text-[0.7rem] text-ink-faint">
                      {e.ts.toLocaleString("tr-TR")} · {s.label}
                      {e.status === "success" && ` · ${rows.toLocaleString("tr-TR")} satır`}
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-ink-faint transition-colors group-hover:text-brand" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </ViewShell>
  );
}
