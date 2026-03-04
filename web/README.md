# KYCC Frontend

React 19 + Vite 7 + TypeScript single-page application for Know Your Coin History.

## Development

```bash
npm install
npm run dev      # http://localhost:5173 — proxies /api to :5050
npm run build    # type-check + bundle → dist/
npx tsc -b       # type-check only
```

## Stack

- **React 19** — UI
- **Vite 7** with `@vitejs/plugin-react` — build tool + HMR
- **TypeScript** — strict mode
- **@xyflow/react v12** — interactive graph canvas (React Flow)
- **Zustand** — global state (nodes, edges, theme, labels, sessions)
- **Tailwind CSS v4** via `@tailwindcss/vite` — utility-first styling, configured in `src/index.css`
- **Framer Motion** — spring animations (RightPanel slide, SettingsModal)
- **Sonner** — toast notifications
- **Lucide React** — icons

## Key Files

| File | Purpose |
|------|---------|
| `src/index.css` | Tailwind v4 import, dark mode variant, CSS custom properties, animations |
| `src/store/graph.ts` | Zustand store — nodes, edges, theme, fingerprint, wallet, sessions |
| `src/types/graph.ts` | TypeScript interfaces (TxData, UTXOData, Annotation, SessionData…) |
| `src/api/client.ts` | Typed fetch wrappers for all `/api/*` backend routes |
| `src/components/Toolbar.tsx` | Header — logo, wallet selector, fingerprint toggle, import/export, settings |
| `src/components/Graph/EmptyState.tsx` | Hero landing page — large search, info cards, famous TXs, recent sessions |
| `src/components/Graph/FloatingSearch.tsx` | Compact pill search overlay shown when graph is loaded |
| `src/components/Graph/GraphCanvas.tsx` | React Flow wrapper — renders nodes, edges, overlays |
| `src/components/Graph/TransactionNode.tsx` | 280px TX card with orange top border and fingerprint annotations |
| `src/components/Graph/UTXONode.tsx` | 200px pill UTXO node with value, address, expand button |
| `src/components/RightPanel.tsx` | Label editor + fingerprint detail panel (spring slide-in) |
| `src/components/SettingsModal.tsx` | Node status + heuristic toggles |

## Proxy

`vite.config.ts` proxies `/api` → `http://localhost:5050`. The backend must be running for any data to load.

## Detailed Documentation

See [`docs/FRONTEND.md`](../docs/FRONTEND.md) in the repo root for full component documentation, styling guide, state management details, and API client reference.
