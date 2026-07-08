import { FileBarChart2, Download, Inbox } from "lucide-react";
import { ViewShell } from "./ViewShell";
import { Button } from "../ui/button";
import { downloadCsv, timestamp } from "@/lib/csv";
import type { Entry } from "@/types";

// Raporlar: oturumdaki BAŞARILI analizler (veri döndürenler). Her biri gerçek
// CSV olarak indirilebilir — süs değil, işlevsel.
export function ReportsView({ entries }: { entries: Entry[] }) {
  const reports = entries.filter(
    (e) => e.status === "success" && e.result?.columns && (e.result.rows?.length ?? 0) > 0
  );

  return (
    <ViewShell
      title="Raporlar"
      description="Bu oturumda veri döndüren analizler; her biri CSV olarak indirilebilir."
      icon={<FileBarChart2 className="h-5 w-5" />}
    >
      {reports.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-line-soft bg-surface py-12 text-center">
          <Inbox className="h-6 w-6 text-ink-faint" />
          <p className="text-sm text-ink-muted">Henüz indirilebilir rapor yok. Bir sorgu çalıştırın.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {[...reports].reverse().map((e) => {
            const cols = e.result!.columns!;
            const rows = e.result!.rows!;
            return (
              <div
                key={e.id}
                className="flex items-center gap-3 rounded-lg border border-line-soft bg-surface px-4 py-3 metal-edge"
              >
                <span className="rounded-lg bg-brand/10 p-2 text-brand">
                  <FileBarChart2 className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm text-ink">{e.question}</div>
                  <div className="mt-0.5 text-[0.7rem] text-ink-faint">
                    {e.ts.toLocaleString("tr-TR")} · {rows.length.toLocaleString("tr-TR")} satır · {cols.length} kolon
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadCsv(cols, rows, `rapor_${timestamp(e.ts)}.csv`)}
                >
                  <Download className="h-3.5 w-3.5" />
                  CSV indir
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </ViewShell>
  );
}
