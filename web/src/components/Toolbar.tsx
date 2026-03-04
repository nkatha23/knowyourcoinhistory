import { useRef, useEffect, useState } from 'react';
import { toast } from 'sonner';
import {
  Upload, Download, Eye, EyeOff,
  Settings, Sun, Moon, Wallet, X, Plus,
} from 'lucide-react';
import { useGraphStore } from '../store/graph';
import { exportLabels, importLabels, fetchWallets } from '../api/client';

interface Props {
  onOpenSettings: () => void;
}

export default function Toolbar({ onOpenSettings }: Props) {
  const [wallets, setWallets] = useState<string[]>([]);
  const [newWallet, setNewWallet] = useState('');
  const [showAddWallet, setShowAddWallet] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const toggleFingerprint = useGraphStore((s) => s.toggleFingerprint);
  const toggleTheme = useGraphStore((s) => s.toggleTheme);
  const fingerprintEnabled = useGraphStore((s) => s.fingerprintEnabled);
  const theme = useGraphStore((s) => s.theme);
  const backendOnline = useGraphStore((s) => s.backendOnline);
  const walletId = useGraphStore((s) => s.walletId);
  const setWalletId = useGraphStore((s) => s.setWalletId);

  useEffect(() => {
    if (!backendOnline) return;
    fetchWallets()
      .then((r) => setWallets(r.wallets))
      .catch(() => setWallets(['default']));
  }, [backendOnline]);

  const walletOptions = wallets.includes(walletId)
    ? wallets
    : ['default', ...wallets.filter((w) => w !== 'default'), walletId];

  async function handleExport() {
    try {
      await exportLabels(walletId);
      toast.success('Labels exported');
    } catch {
      toast.error('Export failed');
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await importLabels(file, walletId);
      toast.success(`Imported ${result.imported} labels`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Import failed');
    } finally {
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  function handleAddWallet() {
    const name = newWallet.trim();
    if (!name) return;
    if (!wallets.includes(name)) setWallets((w) => [...w, name]);
    setWalletId(name);
    setNewWallet('');
    setShowAddWallet(false);
    toast.success(`Switched to wallet "${name}"`);
  }

  return (
    <header className="h-14 flex items-center gap-3 px-4 border-b border-[var(--border)] bg-[var(--bg)] shrink-0 z-20">
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xl font-bold text-[var(--color-btc)]">₿</span>
        <span
          className="hidden sm:block text-[var(--fg)] leading-tight"
          style={{ fontSize: 18, fontWeight: 600 }}
        >
          Know Your<br />Coin History
        </span>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Backend status dot */}
      <div
        className="flex items-center gap-1.5 text-xs shrink-0"
        title={backendOnline ? 'Bitcoin node connected' : 'Backend offline — check Settings'}
      >
        <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-green-500' : 'bg-red-400'}`} />
        <span className="hidden md:inline text-[var(--fg-muted)]">
          {backendOnline ? 'Online' : 'Offline'}
        </span>
      </div>

      <div className="h-6 w-px bg-[var(--border)] shrink-0" />

      {/* Wallet selector */}
      <div className="flex items-center gap-1 shrink-0">
        <Wallet className="w-3.5 h-3.5 text-[var(--fg-muted)] shrink-0" />
        {showAddWallet ? (
          <div className="flex items-center gap-1">
            <input
              autoFocus
              type="text"
              value={newWallet}
              onChange={(e) => setNewWallet(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddWallet()}
              onBlur={() => { if (!newWallet) setShowAddWallet(false); }}
              placeholder="wallet name"
              className="h-8 w-28 px-2 text-xs rounded-lg border border-[var(--color-btc)] bg-[var(--bg-subtle)] text-[var(--fg)] focus:outline-none font-mono"
            />
            <button
              onClick={handleAddWallet}
              className="h-8 px-2 rounded-lg bg-[var(--color-btc)] text-white text-xs font-semibold"
            >
              Add
            </button>
            <button
              onClick={() => setShowAddWallet(false)}
              className="h-8 px-1 text-[var(--fg-muted)] hover:text-[var(--fg)]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <>
            <select
              value={walletId}
              onChange={(e) => setWalletId(e.target.value)}
              className="h-8 px-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)] text-[var(--fg)] focus:outline-none focus:ring-2 focus:ring-[var(--color-btc)]/40"
            >
              {walletOptions.map((w) => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
            <button
              onClick={() => setShowAddWallet(true)}
              title="Add new wallet"
              className="h-8 w-7 flex items-center justify-center rounded-lg text-[var(--fg-muted)] hover:text-[var(--color-btc)] hover:bg-[var(--bg-subtle)] border border-transparent hover:border-[var(--border)] transition"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </>
        )}
      </div>

      <div className="h-6 w-px bg-[var(--border)] shrink-0" />

      {/* Action buttons */}
      <div className="flex items-center gap-1 shrink-0">
        <ToolBtn
          onClick={toggleFingerprint}
          active={fingerprintEnabled}
          title={fingerprintEnabled ? 'Hide all fingerprint annotations' : 'Show fingerprint annotations'}
        >
          {fingerprintEnabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </ToolBtn>

        <ToolBtn onClick={() => fileRef.current?.click()} title="Import labels (.jsonl / BIP-329)">
          <Upload className="w-4 h-4" />
        </ToolBtn>
        <input ref={fileRef} type="file" accept=".jsonl,.json" className="hidden" onChange={handleImport} />

        <ToolBtn onClick={handleExport} title="Export labels (.jsonl / BIP-329)">
          <Download className="w-4 h-4" />
        </ToolBtn>

        <ToolBtn
          onClick={toggleTheme}
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </ToolBtn>

        <ToolBtn onClick={onOpenSettings} title="Settings">
          <Settings className="w-4 h-4" />
        </ToolBtn>
      </div>
    </header>
  );
}

function ToolBtn({
  children, onClick, title, active,
}: {
  children: React.ReactNode;
  onClick: () => void;
  title: string;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`w-8 h-8 rounded-lg flex items-center justify-center transition
        ${active
          ? 'bg-[var(--color-btc)] text-white'
          : 'text-[var(--fg-muted)] hover:text-[var(--fg)] hover:bg-[var(--bg-subtle)] border border-transparent hover:border-[var(--border)]'
        }`}
    >
      {children}
    </button>
  );
}
