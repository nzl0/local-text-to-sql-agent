import type { ReactNode } from "react";

interface ViewShellProps {
  title: string;
  description: string;
  icon: ReactNode;
  children: ReactNode;
}

// Sol nav görünümleri için ortak kurumsal başlık + içerik kabuğu.
export function ViewShell({ title, description, icon, children }: ViewShellProps) {
  return (
    <div className="animate-fade-in py-8">
      <div className="mb-6 flex items-start gap-3">
        <span className="mt-0.5 rounded-lg border border-line-soft bg-raised p-2 text-brand metal-edge">{icon}</span>
        <div>
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          <p className="mt-0.5 text-sm text-ink-muted">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}
