// Backend sözleşmesinin (agent.py AgentResult + api.py SSE) TypeScript aynası.
// Alan adları koddan çıkarıldı; hiçbiri tahmin değil.

export type Row = Record<string, unknown>;

export interface AutoFix {
  attempt: number;
  error: string;
  broken_sql: string;
  fixed_sql: string;
}

// api.py 'result' olayının taşıdığı tam AgentResult (dataclasses.asdict).
export interface AgentResult {
  question: string;
  tables: string[];
  sql: string;
  columns: string[] | null;
  rows: Row[] | null;
  insight: string;
  retry_count: number;
  auto_fixes: AutoFix[];
  error: string | null;
}

// Canlı SSE aşama anahtarları (backend'de gerçekten gözlemlenebilir metotlar).
export type StageKey = "bulma" | "uretim" | "calistirma" | "yorumlama";
export type StagePhase = "start" | "done" | "error";
export type StageState = "bekliyor" | "calisiyor" | "tamam" | "hata";

// Sol navigasyon görünümleri.
export type ViewKey = "home" | "sources" | "history" | "reports" | "security";

// /api/sources — Veri Kaynakları paneli.
export interface SourceColumn {
  name: string;
  type: string;
  description: string;
}
export interface SourceTable {
  name: string;
  file: string;
  description: string;
  columns: SourceColumn[];
}

// /api/security — Güvenlik Kontrolleri paneli.
export interface SecurityInfo {
  db_connected: boolean;
  table_count: number;
  engine: string;
  model: string;
  readonly: boolean;
  local_only: boolean;
  classification: string;
}

// Bir sohbet kaydının UI durumu.
export type EntryStatus = "processing" | "success" | "empty" | "error";

export interface Entry {
  id: number;
  question: string;
  ts: Date;
  status: EntryStatus;
  // Canlı ilerleme
  stages: Record<StageKey, StageState>;
  liveFixes: AutoFix[]; // akış sırasında gelen fix olayları (turuncu not)
  liveInsight: string; // token-token birikirken
  streaming: boolean; // insight hâlâ akıyor mu (imleç için)
  // Nihai sonuç (result olayı gelince dolar)
  result: AgentResult | null;
}
