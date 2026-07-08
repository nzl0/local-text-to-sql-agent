import type { AgentResult, AutoFix, SecurityInfo, SourceTable, StageKey, StagePhase } from "@/types";

// Salt-okunur yardımcı uç noktalar (sol nav panelleri + statü paneli).
export async function fetchSources(): Promise<SourceTable[]> {
  const r = await fetch("/api/sources");
  if (!r.ok) throw new Error("sources");
  return r.json();
}

export async function fetchSecurity(): Promise<SecurityInfo> {
  const r = await fetch("/api/security");
  if (!r.ok) throw new Error("security");
  return r.json();
}

export interface HealthInfo {
  status: string;
  tables: string[];
  data_ok: boolean;
}

export async function fetchHealth(): Promise<HealthInfo> {
  const r = await fetch("/api/health");
  if (!r.ok) throw new Error("health");
  return r.json();
}

// SSE olay işleyicileri. api.py'nin yayınladığı olay kontratıyla birebir.
export interface StreamHandlers {
  onStage: (key: StageKey, phase: StagePhase, extra: Record<string, unknown>) => void;
  onFix: (fix: AutoFix) => void;
  onInsightToken: (token: string) => void;
  onResult: (result: AgentResult) => void;
  onAgentError: (message: string) => void;
  onDone: () => void;
  // Bağlantı düzeyinde hata (sunucuya ulaşılamadı vb.)
  onConnectionError: () => void;
}

/**
 * /api/ask SSE akışını açar. Backend'e HİÇBİR ek istek atmaz; tek bir
 * EventSource bağlantısı kurar. 'done' gelince ya da hata olunca kapatır.
 * Akışı iptal etmek için döndürülen close() çağrılır.
 */
export function askStream(question: string, handlers: StreamHandlers): () => void {
  const url = `/api/ask?q=${encodeURIComponent(question)}`;
  const es = new EventSource(url);
  let closed = false;

  const close = () => {
    if (!closed) {
      closed = true;
      es.close();
    }
  };

  es.addEventListener("stage", (e) => {
    const d = JSON.parse((e as MessageEvent).data);
    const { key, phase, ...extra } = d;
    handlers.onStage(key, phase, extra);
  });

  es.addEventListener("fix", (e) => {
    handlers.onFix(JSON.parse((e as MessageEvent).data));
  });

  es.addEventListener("insight", (e) => {
    const d = JSON.parse((e as MessageEvent).data);
    handlers.onInsightToken(d.token);
  });

  es.addEventListener("result", (e) => {
    handlers.onResult(JSON.parse((e as MessageEvent).data));
  });

  es.addEventListener("agent_error", (e) => {
    const d = JSON.parse((e as MessageEvent).data);
    handlers.onAgentError(d.message);
  });

  es.addEventListener("done", () => {
    handlers.onDone();
    close();
  });

  // EventSource'un yerleşik hata olayı: yalnızca akış 'done' ile düzgün
  // kapanmadan bağlantı koparsa gerçek bir sorundur.
  es.onerror = () => {
    if (closed) return;
    close();
    handlers.onConnectionError();
  };

  return close;
}
