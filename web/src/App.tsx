import { useState, useRef, useCallback, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { EmptyState } from "./components/EmptyState";
import { QuestionInput } from "./components/QuestionInput";
import { MessageCard } from "./components/MessageCard";
import { SourcesView } from "./components/views/SourcesView";
import { HistoryView } from "./components/views/HistoryView";
import { ReportsView } from "./components/views/ReportsView";
import { SecurityView } from "./components/views/SecurityView";
import { askStream } from "./lib/api";
import type { Entry, StageKey, StageState, ViewKey } from "./types";

const EMPTY_STAGES = (): Record<StageKey, StageState> => ({
  bulma: "bekliyor",
  uretim: "bekliyor",
  calistirma: "bekliyor",
  yorumlama: "bekliyor",
});

export default function App() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<ViewKey>("home");
  const [collapsed, setCollapsed] = useState(false);
  const idRef = useRef(0);
  const closeRef = useRef<(() => void) | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const updateEntry = useCallback((id: number, patch: (e: Entry) => Partial<Entry>) => {
    setEntries((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch(e) } : e)));
  }, []);

  // Ana Sayfa'da yeni kayıt eklenince en alta kaydır.
  useEffect(() => {
    if (view === "home") bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [entries.length, view]);

  const submit = useCallback(
    (question: string) => {
      if (busy) return;
      setView("home");
      const id = ++idRef.current;
      const entry: Entry = {
        id,
        question,
        ts: new Date(),
        status: "processing",
        stages: EMPTY_STAGES(),
        liveFixes: [],
        liveInsight: "",
        streaming: false,
        result: null,
      };
      setEntries((prev) => [...prev, entry]);
      setBusy(true);

      closeRef.current = askStream(question, {
        onStage: (key, phase) => {
          updateEntry(id, (e) => {
            const stages = { ...e.stages };
            if (phase === "start") stages[key] = "calisiyor";
            else if (phase === "done") stages[key] = "tamam";
            return { stages };
          });
        },
        onFix: (fix) => {
          updateEntry(id, (e) => ({ liveFixes: [...e.liveFixes, fix] }));
        },
        onInsightToken: (token) => {
          updateEntry(id, (e) => ({
            liveInsight: e.liveInsight + token,
            streaming: true,
            stages: { ...e.stages, yorumlama: "calisiyor" },
          }));
        },
        onResult: (result) => {
          const status =
            result.error != null
              ? "error"
              : result.rows && result.rows.length === 0
                ? "empty"
                : "success";
          updateEntry(id, () => ({ result, status }));
        },
        onAgentError: (message) => {
          updateEntry(id, (e) => ({
            status: "error",
            result: {
              question: e.question,
              tables: [],
              sql: "",
              columns: null,
              rows: null,
              insight: "",
              retry_count: 0,
              auto_fixes: [],
              error: message,
            },
          }));
        },
        onDone: () => {
          updateEntry(id, () => ({ streaming: false }));
          setBusy(false);
          closeRef.current = null;
        },
        onConnectionError: () => {
          updateEntry(id, (e) =>
            e.status === "processing"
              ? {
                  status: "error",
                  streaming: false,
                  result: {
                    question: e.question,
                    tables: [],
                    sql: "",
                    columns: null,
                    rows: null,
                    insight: "",
                    retry_count: 0,
                    auto_fixes: [],
                    error: "Sunucuya ulaşılamadı. Yerel servisin çalıştığından emin olun.",
                  },
                }
              : {}
          );
          setBusy(false);
          closeRef.current = null;
        },
      });
    },
    [busy, updateEntry]
  );

  const newChat = useCallback(() => {
    closeRef.current?.();
    closeRef.current = null;
    setEntries([]);
    setBusy(false);
    setView("home");
  }, []);

  // Geçmiş'ten bir analize atla.
  const openEntry = useCallback((entryId: number) => {
    setView("home");
    setTimeout(() => {
      document.getElementById(`entry-${entryId}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 60);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        view={view}
        onSelect={setView}
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        historyCount={entries.length}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onNewChat={newChat} busy={busy} />

        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-4xl px-4 sm:px-6">
            {view === "home" && (
              <>
                {entries.length === 0 ? (
                  <EmptyState onPick={submit} disabled={busy} />
                ) : (
                  <div className="space-y-4 py-6">
                    {entries.map((entry) => (
                      <MessageCard key={entry.id} entry={entry} onRetry={submit} retryDisabled={busy} />
                    ))}
                  </div>
                )}
                <div ref={bottomRef} />
              </>
            )}

            {view === "sources" && <SourcesView />}
            {view === "history" && <HistoryView entries={entries} onOpen={openEntry} />}
            {view === "reports" && <ReportsView entries={entries} />}
            {view === "security" && <SecurityView />}
          </div>
        </div>

        {view === "home" && <QuestionInput onSubmit={submit} busy={busy} />}
      </div>
    </div>
  );
}
