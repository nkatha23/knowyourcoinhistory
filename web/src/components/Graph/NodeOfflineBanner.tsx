import { AlertTriangle, Settings } from 'lucide-react';

interface Props {
  onOpenSettings: () => void;
}

export default function NodeOfflineBanner({ onOpenSettings }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl border border-amber-200 dark:border-amber-700/60 bg-amber-50 dark:bg-amber-950/30">
      <div className="flex items-center gap-2.5 min-w-0">
        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
        <p className="text-sm text-[var(--fg)]">
          <span className="font-semibold">Bitcoin node unreachable.</span>{' '}
          <span className="text-[var(--fg-muted)]">Configure your node to explore transactions.</span>
        </p>
      </div>
      <button
        onClick={onOpenSettings}
        className="shrink-0 flex items-center gap-1.5 h-8 px-3 rounded-lg text-sm font-semibold bg-amber-500 text-white hover:bg-amber-600 transition"
      >
        <Settings className="w-3.5 h-3.5" />
        Settings
      </button>
    </div>
  );
}
