import { cn } from "@/lib/utils";

/**
 * ASELSAN logo yuvası.
 *
 * Resmi logo dosyası `web/src/assets/aselsan-logo.svg` (veya .png/.webp) olarak
 * bırakıldığında OTOMATİK olarak kullanılır. Dosya yokken, kurumun amblemini
 * TAKLİT ETMEYEN, salt tipografik bir "aselsan" wordmark placeholder gösterilir
 * (tech-blue). Böylece düzen bozulmaz ve marka aslına sadık olmayan bir şekilde
 * yeniden çizilmez.
 *
 * Not: `import.meta.glob` eager+url ile dosya yoksa derleme kırılmaz (boş küme).
 */
const logoMods = import.meta.glob("../assets/aselsan-logo.{svg,png,webp}", {
  eager: true,
  query: "?url",
  import: "default",
});
const LOGO_URL = Object.values(logoMods)[0] as string | undefined;

interface LogoMarkProps {
  /** Yükseklik sınıfı, ör. "h-7" (header) veya "h-6" (mini sağ üst). */
  className?: string;
  /** Placeholder wordmark boyutu. */
  wordmarkClassName?: string;
}

export function LogoMark({ className, wordmarkClassName }: LogoMarkProps) {
  if (LOGO_URL) {
    return <img src={LOGO_URL} alt="ASELSAN" className={cn("w-auto object-contain", className)} draggable={false} />;
  }
  // Tipografik placeholder — amblem yok, yalnızca kelime-logo.
  return (
    <span
      className={cn(
        "font-semibold lowercase leading-none tracking-tight text-brand",
        wordmarkClassName ?? "text-lg"
      )}
      aria-label="ASELSAN"
    >
      aselsan
    </span>
  );
}

/** Resmi logo dosyasının yerinde olup olmadığı (placeholder uyarısı için). */
export const HAS_OFFICIAL_LOGO = Boolean(LOGO_URL);
