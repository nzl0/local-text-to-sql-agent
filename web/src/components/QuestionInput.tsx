import { useState, useRef, useEffect } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuestionInputProps {
  onSubmit: (q: string) => void;
  busy: boolean;
}

// Alt sabit giriş: Enter ile gönderim (Shift+Enter satır atlar). İşlem sürerken
// kilitli ve bunu görsel olarak (soluk, spinner, "işleniyor" ipucu) belli eder.
export function QuestionInput({ onSubmit, busy }: QuestionInputProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // İşlem bitince girişe odağı geri ver.
  useEffect(() => {
    if (!busy) ref.current?.focus();
  }, [busy]);

  // Otomatik yükseklik (tek satırdan birkaç satıra).
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [value]);

  const submit = () => {
    const q = value.trim();
    if (!q || busy) return;
    onSubmit(q);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const canSend = value.trim().length > 0 && !busy;

  return (
    <div className="pointer-events-none sticky bottom-0 z-20 bg-gradient-to-t from-bg via-bg/95 to-transparent pt-6">
      <div className="mx-auto max-w-4xl px-4 pb-4 sm:px-6">
        <div
          className={cn(
            "pointer-events-auto flex items-end gap-2 rounded-2xl border bg-raised p-2 shadow-card transition-colors duration-150",
            busy ? "border-line-soft opacity-80" : "border-line focus-within:border-brand/60"
          )}
        >
          <textarea
            ref={ref}
            rows={1}
            value={value}
            disabled={busy}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={busy ? "Yanıt hazırlanıyor…" : "Bir soru sorun…"}
            className="max-h-40 flex-1 resize-none bg-transparent px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:outline-none disabled:cursor-not-allowed"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Gönder"
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all duration-150",
              canSend
                ? "bg-brand text-white hover:bg-brand-hi active:translate-y-px"
                : "cursor-not-allowed bg-white/5 text-ink-faint"
            )}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-1.5 px-1 text-center text-[0.7rem] text-ink-faint">
          {busy
            ? "Sistem soruyu işliyor — lütfen bekleyin."
            : "Enter ile gönder · Shift+Enter ile satır atla"}
        </p>
      </div>
    </div>
  );
}
