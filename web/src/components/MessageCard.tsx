import { RotateCw, SearchX, AlertCircle, ChevronDown } from "lucide-react";
import { Button } from "./ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import { StageTracker } from "./StageTracker";
import { ResultTable } from "./ResultTable";
import { InsightText } from "./InsightText";
import type { Entry } from "@/types";

interface MessageCardProps {
  entry: Entry;
  onRetry: (q: string) => void;
  retryDisabled: boolean;
}

export function MessageCard({ entry, onRetry, retryDisabled }: MessageCardProps) {
  const { question, status, result, stages, liveFixes, liveInsight, streaming } = entry;

  return (
    <article
      id={`entry-${entry.id}`}
      className="animate-fade-in scroll-mt-20 rounded-xl border border-line-soft bg-surface p-5 shadow-card transition-shadow duration-150 hover:shadow-card-hover"
    >
      {/* Soru başlığı — mavi ince sol çizgi */}
      <div className="mb-4 border-l-2 border-brand pl-3 text-[0.98rem] font-semibold text-ink">
        {question}
      </div>

      {/* İŞLENİYOR */}
      {status === "processing" && (
        <>
          <StageTracker stages={stages} liveFixes={liveFixes} />
          {liveInsight && <InsightText text={liveInsight} streaming={streaming} />}
        </>
      )}

      {/* HATA — boş sonuçtan görsel olarak ayrı, desatüre kırmızı */}
      {status === "error" && result && (
        <div>
          <div className="flex items-start gap-3 rounded-lg border border-danger-line bg-danger-dim p-3.5">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-danger">Sorgunuz çalıştırılamadı</div>
              <div className="mt-0.5 text-xs text-ink-muted">
                Soruyu daha belirgin ifade etmeyi deneyebilir ya da yeniden gönderebilirsiniz.
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => onRetry(question)} disabled={retryDisabled}>
              <RotateCw className="h-3.5 w-3.5" />
              Tekrar dene
            </Button>
          </div>

          {/* Teknik detay — katlanabilir (yalnızca hata mesajı; SQL gösterilmez) */}
          {result.error && (
            <Collapsible className="mt-3">
              <CollapsibleTrigger className="group flex items-center gap-1.5 text-xs text-ink-faint transition-colors hover:text-ink-muted">
                <ChevronDown className="h-3.5 w-3.5 transition-transform group-data-[state=open]:rotate-180" />
                Teknik detay
              </CollapsibleTrigger>
              <CollapsibleContent className="overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
                <div className="pt-2">
                  <pre className="overflow-x-auto rounded-lg border border-line-soft bg-bg/60 p-3 font-mono text-[0.72rem] leading-relaxed text-danger">
                    {result.error}
                  </pre>
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </div>
      )}

      {/* BOŞ SONUÇ — sakin durum, hatadan ayrı */}
      {status === "empty" && result && (
        <div>
          <div className="flex items-start gap-3 rounded-lg border border-line-soft bg-raised p-3.5">
            <SearchX className="mt-0.5 h-4 w-4 shrink-0 text-ink-muted" />
            <div>
              <div className="text-sm text-ink">Bu kriterlere uyan kayıt bulunamadı</div>
              <div className="mt-0.5 text-xs text-ink-muted">
                Tarih aralığını genişletmeyi ya da farklı bir kategori/ürün adı denemeyi
                düşünebilirsiniz.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* BAŞARI — tablo önce, yorum ikincil */}
      {status === "success" && result && result.columns && result.rows && (
        <div>
          <ResultTable columns={result.columns} rows={result.rows} ts={entry.ts} />
          <InsightText text={liveInsight || result.insight} streaming={streaming} />
        </div>
      )}
    </article>
  );
}
