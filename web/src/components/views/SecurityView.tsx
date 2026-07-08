import { useEffect, useState, type ReactNode } from "react";
import { ShieldCheck, Database, Cpu, Lock, WifiOff, Server, Loader2, AlertCircle, CircleCheck } from "lucide-react";
import { fetchSecurity } from "@/lib/api";
import { ViewShell } from "./ViewShell";
import { cn } from "@/lib/utils";
import type { SecurityInfo } from "@/types";

// Güvenlik Kontrolleri: GERÇEK güvenlik/bağlantı durumu (/api/security) +
// tarayıcı çevrimdışı durumu. Her gösterge canlı veriden beslenir.
export function SecurityView() {
  const [info, setInfo] = useState<SecurityInfo | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    fetchSecurity()
      .then((d) => alive && setInfo(d))
      .catch(() => alive && setError(true));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <ViewShell
      title="Güvenlik Kontrolleri"
      description="Sistemin güvenlik duruşu ve veri erişim güvencesi."
      icon={<ShieldCheck className="h-5 w-5" />}
    >
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-danger-line bg-danger-dim p-3 text-sm text-danger">
          <AlertCircle className="h-4 w-4" /> Güvenlik durumu alınamadı.
        </div>
      )}
      {!error && !info && (
        <div className="flex items-center gap-2 text-sm text-ink-muted">
          <Loader2 className="h-4 w-4 animate-spin" /> Denetleniyor…
        </div>
      )}
      {info && (
        <div className="space-y-4">
          {/* Sınıflandırma bandı */}
          <div className="flex items-center justify-between rounded-xl border border-gold-line bg-gold-dim px-5 py-4">
            <div className="flex items-center gap-3">
              <Lock className="h-5 w-5 text-gold" />
              <div>
                <div className="text-[0.7rem] uppercase tracking-wider text-gold/80">Gizlilik Seviyesi</div>
                <div className="text-lg font-bold text-gold">{info.classification}</div>
              </div>
            </div>
            <span className="text-[0.7rem] text-ink-muted">Kurumsal sınıflandırma</span>
          </div>

          {/* Güvenlik göstergeleri */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Check
              ok={info.db_connected}
              icon={<Database className="h-4 w-4" />}
              title="Veri Tabanı Bağlantısı"
              value={info.db_connected ? "Aktif" : "Bağlı değil"}
            />
            <Check
              ok={info.local_only}
              icon={<WifiOff className="h-4 w-4" />}
              title="Yerel Çalışma"
              value={info.local_only ? "Yalnızca yerel · dış ağ isteği yok" : "—"}
            />
            <Check
              ok={info.readonly}
              icon={<Lock className="h-4 w-4" />}
              title="Veri Erişimi"
              value={info.readonly ? "Salt-okunur (bellek içi)" : "—"}
            />
            <Info icon={<Server className="h-4 w-4" />} title="Sorgu Motoru" value={info.engine} />
            <Info icon={<Cpu className="h-4 w-4" />} title="Dil Modeli" value={`${info.model} (yerel)`} />
            <Info icon={<Database className="h-4 w-4" />} title="Kayıtlı Tablo" value={`${info.table_count} tablo`} />
          </div>
        </div>
      )}
    </ViewShell>
  );
}

function Check({ ok, icon, title, value }: { ok: boolean; icon: ReactNode; title: string; value: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-line-soft bg-surface p-4 metal-edge">
      <span className={cn("rounded-lg p-2", ok ? "bg-ok/12 text-ok" : "bg-danger/12 text-danger")}>{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-sm font-medium text-ink">
          {title}
          {ok && <CircleCheck className="h-3.5 w-3.5 text-ok" />}
        </div>
        <div className="mt-0.5 text-xs text-ink-muted">{value}</div>
      </div>
    </div>
  );
}

function Info({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-line-soft bg-surface p-4 metal-edge">
      <span className="rounded-lg bg-brand/10 p-2 text-brand">{icon}</span>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium text-ink">{title}</div>
        <div className="mt-0.5 truncate text-xs text-ink-muted">{value}</div>
      </div>
    </div>
  );
}
