import { SquarePen } from "lucide-react";
import { Button } from "./ui/button";
import { LogoMark } from "./LogoMark";
import { StatusPanel } from "./StatusPanel";

interface HeaderProps {
  onNewChat: () => void;
  busy: boolean;
}

// Kurumsal başlık çubuğu.
// Sol: ASELSAN logo + HBT_AGENT + alt başlık.
// Sağ: statü paneli (DB bağlantısı + gizlilik) + Yeni Sohbet + mini logo.
export function Header({ onNewChat, busy }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-line-soft bg-bg/85 backdrop-blur-md">
      <div className="flex items-center gap-3 px-4 py-2.5 sm:px-6">
        {/* SOL: logo + isim */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <LogoMark className="h-7" wordmarkClassName="text-lg" />
          <span className="h-8 w-px metal-divider" aria-hidden="true" />
          <div className="flex min-w-0 flex-col">
            <h1 className="text-[1.02rem] font-bold leading-tight tracking-wide text-brand">HBT_AGENT</h1>
            <p className="truncate text-[0.72rem] leading-tight text-ink-muted">
              Üretim ve planlama verileri için doğal dil sorgu asistanı
            </p>
          </div>
        </div>

        {/* SAĞ: statü + eylem + mini logo */}
        <div className="flex items-center gap-3">
          <StatusPanel />
          <Button variant="outline" size="sm" onClick={onNewChat} disabled={busy}>
            <SquarePen className="h-4 w-4" />
            <span className="hidden sm:inline">Yeni Sohbet</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
