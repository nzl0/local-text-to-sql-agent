import { useMemo } from "react";
import { Download } from "lucide-react";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";
import { downloadCsv, timestamp } from "@/lib/csv";
import type { Row } from "@/types";

interface ResultTableProps {
  columns: string[];
  rows: Row[];
  ts: Date;
}

function isNumeric(v: unknown): boolean {
  return typeof v === "number" && !Number.isNaN(v);
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") return v.toLocaleString("tr-TR");
  return String(v);
}

export function ResultTable({ columns, rows, ts }: ResultTableProps) {
  // Bir kolon, boş olmayan tüm değerleri sayıysa sayısaldır → sağa dayalı + mono.
  const numericCols = useMemo(() => {
    const set = new Set<string>();
    for (const c of columns) {
      const vals = rows.map((r) => r[c]).filter((v) => v !== null && v !== undefined && v !== "");
      if (vals.length > 0 && vals.every(isNumeric)) set.add(c);
    }
    return set;
  }, [columns, rows]);

  const onDownload = () => downloadCsv(columns, rows, `sonuc_${timestamp(ts)}.csv`);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs text-ink-muted">
          {rows.length.toLocaleString("tr-TR")} satır · {columns.length} kolon
        </span>
        <Button variant="outline" size="sm" onClick={onDownload}>
          <Download className="h-3.5 w-3.5" />
          CSV indir
        </Button>
      </div>

      <div className="max-h-[26rem] overflow-auto rounded-lg border border-line-soft">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-raised">
              {columns.map((c) => (
                <th
                  key={c}
                  className={cn(
                    "whitespace-nowrap border-b border-line px-3 py-2 font-semibold text-ink-muted",
                    numericCols.has(c) ? "text-right font-mono" : "text-left"
                  )}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="transition-colors hover:bg-white/[0.03]">
                {columns.map((c) => (
                  <td
                    key={c}
                    className={cn(
                      "whitespace-nowrap border-b border-line-soft px-3 py-1.5",
                      numericCols.has(c)
                        ? "text-right font-mono tabular-nums text-ink"
                        : "text-left text-ink"
                    )}
                  >
                    {formatCell(r[c])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
