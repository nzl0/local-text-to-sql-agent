import { ArrowUpRight, Workflow, Component, Waypoints, Radar } from "lucide-react";

// Örnek sorular backend'in gerçek şemasıyla uyumlu (kategori_tanim, stok_hareketi).
// Tıklanınca doğrudan gönderilir — süs değil, işlevsel giriş noktası.
// İkonlar: veri akışı, ürün bileşeni, üretim hattı, radar/tarama.
const EXAMPLES = [
  { icon: Workflow, text: "Geçen hafta en çok sipariş edilen kategori hangisi?" },
  { icon: Component, text: "Depo stoğu 100 birimin altında olan ürünler hangileri?" },
  { icon: Waypoints, text: "Üretimi hiç yapılmamış ürünler hangileri?" },
  { icon: Radar, text: "Elektronik kategorisindeki toplam depo stoğu ne kadar?" },
];

interface EmptyStateProps {
  onPick: (q: string) => void;
  disabled: boolean;
}

export function EmptyState({ onPick, disabled }: EmptyStateProps) {
  return (
    <div className="animate-fade-in py-10">
      <div className="mb-5 flex flex-col items-center text-center">
        <h2 className="text-lg font-semibold text-ink">Örnek veri analizleri ile başlayın:</h2>
        <p className="mt-1 max-w-md text-sm text-ink-muted">
          Aşağıdaki sorulardan birine tıklayın ya da alttaki kutuya kendi sorunuzu yazın.
          Sistem soruyu çalıştırır, veriyi getirir ve yorumlar.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {EXAMPLES.map(({ icon: Icon, text }) => (
          <button
            key={text}
            type="button"
            disabled={disabled}
            onClick={() => onPick(text)}
            className="group flex items-start gap-3 rounded-xl border border-line-soft bg-surface p-4 text-left shadow-card transition-all duration-150 ease-out hover:-translate-y-0.5 hover:border-brand/50 hover:shadow-card-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:pointer-events-none disabled:opacity-50"
          >
            <span className="mt-0.5 rounded-lg bg-brand/10 p-2 text-brand transition-colors group-hover:bg-brand/15">
              <Icon className="h-4 w-4" />
            </span>
            <span className="flex-1 text-sm leading-snug text-ink">{text}</span>
            <ArrowUpRight className="h-4 w-4 shrink-0 text-ink-faint transition-colors group-hover:text-brand" />
          </button>
        ))}
      </div>
    </div>
  );
}
