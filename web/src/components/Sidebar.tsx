import { Home, Database, History, FileBarChart2, ShieldCheck, PanelLeftClose, PanelLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ViewKey } from "@/types";

const NAV: { key: ViewKey; label: string; icon: typeof Home }[] = [
  { key: "home", label: "Ana Sayfa", icon: Home },
  { key: "sources", label: "Veri Kaynakları", icon: Database },
  { key: "history", label: "Geçmiş Analizler", icon: History },
  { key: "reports", label: "Raporlar", icon: FileBarChart2 },
  { key: "security", label: "Güvenlik Kontrolleri", icon: ShieldCheck },
];

interface SidebarProps {
  view: ViewKey;
  onSelect: (v: ViewKey) => void;
  collapsed: boolean;
  onToggle: () => void;
  historyCount: number;
}

export function Sidebar({ view, onSelect, collapsed, onToggle, historyCount }: SidebarProps) {
  return (
    <aside
      className={cn(
        "relative z-30 flex shrink-0 flex-col border-r border-line-soft bg-sidebar transition-[width] duration-200 ease-out",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Üst: daralt/genişlet */}
      <div className={cn("flex h-14 items-center border-b border-line-soft", collapsed ? "justify-center px-0" : "justify-between px-4")}>
        {!collapsed && (
          <span className="text-[0.68rem] font-semibold uppercase tracking-widest text-ink-faint">Menü</span>
        )}
        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Menüyü genişlet" : "Menüyü daralt"}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-white/5 hover:text-ink"
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </button>
      </div>

      {/* Öğeler */}
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {NAV.map(({ key, label, icon: Icon }) => {
          const active = view === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onSelect(key)}
              title={collapsed ? label : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-150",
                collapsed && "justify-center px-0",
                active
                  ? "bg-brand/12 text-ink"
                  : "text-ink-muted hover:bg-white/5 hover:text-ink"
              )}
            >
              {/* Aktif göstergesi — sol mavi çubuk */}
              {active && (
                <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-full bg-brand shadow-brand-glow" />
              )}
              <Icon className={cn("h-[1.05rem] w-[1.05rem] shrink-0", active ? "text-brand" : "text-ink-muted group-hover:text-ink")} />
              {!collapsed && <span className="flex-1 truncate text-left">{label}</span>}
              {/* Geçmiş sayacı — gerçek veriden */}
              {!collapsed && key === "history" && historyCount > 0 && (
                <span className="rounded-full bg-white/8 px-1.5 py-0.5 text-[0.65rem] text-ink-muted">{historyCount}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Alt: küçük kurumsal alt bilgi */}
      {!collapsed && (
        <div className="border-t border-line-soft px-4 py-3">
          <div className="text-[0.62rem] uppercase tracking-widest text-ink-faint">HBT_AGENT</div>
          <div className="mt-0.5 text-[0.62rem] text-ink-faint">Yerel · Sürüm 1.0</div>
        </div>
      )}
    </aside>
  );
}
