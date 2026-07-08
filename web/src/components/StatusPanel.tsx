import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Sağ üst statü alanı:
 *  - Veri Tabanı Bağlantısı: GERÇEK — /api/health'i periyodik yoklar.
 *  - Gizlilik Seviyesi: GİZLİ — statik kurumsal sınıflandırma etiketi
 *    (bir kontrol değil, bilgi amaçlı sabit rozet).
 */
export function StatusPanel() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const h = await fetchHealth();
        if (alive) setConnected(h.status === "ok" && h.data_ok);
      } catch {
        if (alive) setConnected(false);
      }
    };
    check();
    const id = setInterval(check, 15000); // gerçek, canlı yoklama
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const label = connected === null ? "Denetleniyor…" : connected ? "Aktif" : "Bağlı değil";

  return (
    <div className="hidden items-stretch gap-2 lg:flex">
      {/* Veri Tabanı Bağlantısı */}
      <div className="flex flex-col justify-center rounded-lg border border-line-soft bg-raised px-3 py-1.5 metal-edge">
        <span className="text-[0.6rem] uppercase tracking-wider text-ink-faint">Veri Tabanı Bağlantısı</span>
        <span className="mt-0.5 flex items-center gap-1.5 text-xs font-medium text-ink">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              connected === null
                ? "bg-ink-faint"
                : connected
                  ? "bg-ok shadow-[0_0_8px_1px_var(--tw-shadow-color)] shadow-ok/70"
                  : "bg-danger"
            )}
          />
          {label}
        </span>
      </div>
    </div>
  );
}
