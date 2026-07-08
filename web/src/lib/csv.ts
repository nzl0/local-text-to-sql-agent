import type { Row } from "@/types";

function pad(n: number) {
  return String(n).padStart(2, "0");
}

export function timestamp(ts: Date): string {
  return (
    `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}_` +
    `${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`
  );
}

export function toCsv(columns: string[], rows: Row[]): string {
  const esc = (val: unknown) => {
    const s = val === null || val === undefined ? "" : String(val);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = columns.map(esc).join(";");
  const body = rows.map((r) => columns.map((c) => esc(r[c])).join(";")).join("\n");
  return header + "\n" + body;
}

// UTF-8 BOM → Excel Türkçe karakterleri doğru okusun.
export function downloadCsv(columns: string[], rows: Row[], filename: string) {
  const blob = new Blob(["﻿" + toCsv(columns, rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
