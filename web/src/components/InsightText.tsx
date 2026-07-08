import { Sparkles } from "lucide-react";

interface InsightTextProps {
  text: string;
  streaming: boolean;
}

// Yorum: tablo birincil olduğu için görsel olarak İKİNCİL (küçük/soluk).
// Rakamın kaynağı tablodur, yorum çerçevedir — hiyerarşi korunur.
// İmleç yalnızca akış sürerken görünür (gerçek durumu yansıtır).
export function InsightText({ text, streaming }: InsightTextProps) {
  if (!text && !streaming) return null;
  return (
    <div className="mt-3 flex gap-2">
      <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-faint" />
      <p className="text-[0.83rem] leading-relaxed text-ink-muted">
        {text}
        {streaming && (
          <span className="ml-0.5 inline-block h-[0.9em] w-[5px] translate-y-[1px] animate-blink bg-brand align-text-bottom" />
        )}
      </p>
    </div>
  );
}
