import { useEffect, useState } from "react";
import { Database, Table2, Loader2, AlertCircle } from "lucide-react";
import { fetchSources } from "@/lib/api";
import { ViewShell } from "./ViewShell";
import type { SourceTable } from "@/types";

// Veri Kaynakları: GERÇEK katalog (kategori_tanim, stok_hareketi) — /api/sources.
// Ham SQL/DDL gösterilmez; kolonlar okunur biçimde listelenir.
export function SourcesView() {
  const [data, setData] = useState<SourceTable[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchSources()
      .then((d) => alive && setData(d))
      .catch(() => alive && setError(true));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <ViewShell
      title="Veri Kaynakları"
      description="Analizlerde kullanılan yerel veri tabloları ve alanları."
      icon={<Database className="h-5 w-5" />}
    >
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-danger-line bg-danger-dim p-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4" /> Veri kaynakları alınamadı.
        </div>
      )}
      {!error && !data && (
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin" /> Yükleniyor…
        </div>
      )}
      {data && (
        <div className="space-y-4">
          {data.map((t) => (
            <section key={t.name} className="rounded-xl border border-line-soft bg-surface p-5 shadow-card metal-edge">
              <div className="mb-1 flex items-center gap-2">
                <Table2 className="h-4 w-4 text-brand" />
                <h3 className="font-mono text-sm font-semibold text-ink">{t.name}</h3>
                <span className="rounded-md bg-white/5 px-1.5 py-0.5 text-[0.65rem] text-ink-faint">{t.columns.length} alan</span>
              </div>
              {t.description && <p className="mb-3 text-xs leading-relaxed text-ink-muted">{t.description}</p>}
              <div className="overflow-hidden rounded-lg border border-line-soft">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-raised text-left text-[0.7rem] uppercase tracking-wider text-ink-faint">
                      <th className="px-3 py-2 font-semibold">Alan</th>
                      <th className="px-3 py-2 font-semibold">Tür</th>
                      <th className="px-3 py-2 font-semibold">Açıklama</th>
                    </tr>
                  </thead>
                  <tbody>
                    {t.columns.map((c) => (
                      <tr key={c.name} className="border-t border-line-soft">
                        <td className="whitespace-nowrap px-3 py-1.5 font-mono text-xs text-ink">{c.name}</td>
                        <td className="whitespace-nowrap px-3 py-1.5">
                          <span className="rounded bg-brand/10 px-1.5 py-0.5 font-mono text-[0.65rem] text-brand">{c.type}</span>
                        </td>
                        <td className="px-3 py-1.5 text-xs text-ink-muted">{c.description || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}
    </ViewShell>
  );
}
