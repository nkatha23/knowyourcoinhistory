# Frontend Guide

The KYCC frontend is a React 19 single-page application built with Vite 7 and TypeScript. It lives in `web/`.

---

## Running

```bash
cd web
npm install
npm run dev        # http://localhost:5173  (proxies /api → :5050)
npm run build      # production build → dist/
npx tsc -b         # type-check only
```

The Vite dev server proxies all `/api/*` requests to `http://localhost:5050` so the frontend and backend can run on separate ports during development.

---

## Component Overview

### `Toolbar`

Fixed header bar containing:

| Element | Position | Notes |
|---------|----------|-------|
| ₿ logo + "Know Your Coin History" | Left | 18px / weight 600 |
| Backend status dot | Right | Green = online, Red = offline |
| Wallet selector + add button | Right | Persisted to `localStorage` |
| Fingerprint toggle (eye icon) | Right | Orange when active |
| Import button (upload icon) | Right | Accepts `.jsonl` / `.json` |
| Export button (download icon) | Right | Downloads `kycc-labels-{wallet}-{date}.jsonl` |
| Theme toggle (sun/moon) | Right | Persisted to `localStorage` |
| Settings gear | Right | Opens `SettingsModal` |

The search bar was intentionally removed from the toolbar. Search lives on the landing page (`EmptyState`) and in the floating overlay (`FloatingSearch`).

### `EmptyState` — Landing page

Shown when the graph has no nodes. Full-canvas hero layout:

1. **Heading** — "Trace Your Coin History" (48px / 700 / IBM Plex Sans)
2. **Subheading** — 18px grey description
3. **Search box** — 600px wide × 56px tall, JetBrains Mono, 12px border-radius
   - Accepts: 64-char hex txid, or Bitcoin address (`bc1`, `bcrt1`, `1`, `3`)
   - Address search triggers `GET /api/address` and shows a txid dropdown
   - On error: red toast `"Node error: {message}"`
4. **Info cards** — three 180px cards explaining txid, UTXO, BIP-329
5. **Famous Transactions** — two historical reference txids with Copy + Load buttons
6. **Recent Sessions** — up to 4 resumable sessions (loaded from `/api/sessions`)

### `FloatingSearch` — Compact overlay

Shown at the top-centre of the canvas when the graph has nodes. 400px pill shape:

```
[ 🔍 ][ txid or address...       ][ × ][ Search ]  [ ⌂ ]
```

- Same txid/address logic as `EmptyState`
- Address results appear in a dropdown below the pill
- The **⌂ (Home) button** clears the graph and returns to `EmptyState`

### `TransactionNode`

280px wide card with:
- 4px orange top border (always)
- 2px orange glow ring when selected
- Truncated txid in 14px JetBrains Mono / weight 600
- Metadata chips (fee, block, version, vB) at 12px
- Input / Output count summary box
- Orange label tag (when labeled)
- Fingerprint annotation rows (coloured by severity) when fingerprinting is enabled

### `UTXONode`

200px wide pill (20px border-radius) with:
- 3px **green** left border — unspent output
- 3px **gold** left border — coinbase output
- Grey tint on spent inputs
- 16px / 700 JetBrains Mono BTC value (full 8 decimal display)
- 12px sats value below
- 12px truncated address
- Script type badge (P2WPKH, P2TR, P2PKH, P2SH, P2WSH, OP_RETURN…)
- Orange **+** expand button on the left edge for inputs whose parent TX isn't loaded

### `RightPanel`

Spring-animated panel (380px, slides in from the right) when a node is selected:

- Full txid / UTXO outpoint with copy button
- TX details grid: block, fee, input/output count, size, version, RBF, coinbase flags
- UTXO details grid: value in BTC and sats, script type, spend status, full address
- **Label editor** — text input + category dropdown + spendable toggle
  - Saves on blur and on "Save label" button click
  - Skips the API call if the label text is empty (backend rejects empty labels with 400)
  - Delete removes the label from the store
- **Privacy Fingerprints** — expandable list of annotations with severity dot, code, description, and affected addresses

### `SettingsModal`

Framer Motion animated dialog showing:
- **Node Status** — type, network, host:port, block height, online indicator, Re-check button
- **Fingerprint Heuristics** — toggle list for each configured heuristic; `"off in config"` badge for heuristics disabled in `kycc.toml`

---

## Styling

Tailwind CSS v4 via `@tailwindcss/vite`. No `tailwind.config.js` — configuration lives entirely in `web/src/index.css`:

```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --font-sans: "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --color-btc: #f7931a;
  /* ... */
}

:root { /* light mode custom properties */ }
.dark { /* dark mode custom properties */ }
```

Dark mode is class-based (`.dark` on `<html>`). All component colours reference CSS custom properties (`var(--bg)`, `var(--fg)`, `var(--border)`, `var(--node-bg)`, `var(--color-btc)`, etc.) rather than Tailwind colour names, so they automatically respond to the `.dark` class.

---

## State Management

Zustand store (`store/graph.ts`) is the single source of truth. No React context or prop drilling for graph data.

Persistence to `localStorage`:
- `kycc:theme` — `'light'` | `'dark'`
- `kycc:walletId` — selected wallet
- `kycc:hiddenHeuristics` — array of disabled heuristic keys

### Graph layout constants

```typescript
const UTXO_OFFSET = 420;  // px between tx node and UTXO columns
const ROW_GAP     = 110;  // px between vertically stacked UTXOs
const CANVAS_CX   = 500;  // x of root tx node
const CANVAS_CY   = 300;  // y of root tx node
```

### Edge styling

Each edge carries:
- `stroke: '#D1D5DB'`, `strokeWidth: 1.5`
- `animated: true` with a dashed flow animation (left → right)
- A BTC/sat value label rendered at the midpoint

---

## API Client (`api/client.ts`)

Typed wrappers over `fetch`. All calls go to `/api/*` (Vite proxies to `:5050`). On `ok: false` the wrapper throws an `Error` with the server's `error` field as the message — caught by the search handlers and shown as a toast.

| Export | Endpoint |
|--------|----------|
| `fetchHealth` | `GET /api/health` |
| `fetchTx` | `GET /api/tx?txid=` |
| `fetchAddressHistory` | `GET /api/address?address=&wallet_id=` |
| `saveLabel` | `POST /api/label` |
| `deleteLabel` | `DELETE /api/label` |
| `fetchLabels` | `GET /api/labels?wallet_id=` |
| `fetchWallets` | `GET /api/wallets` |
| `fetchSessions` | `GET /api/sessions` |
| `createSession` | `POST /api/session` |
| `exportLabels` | `GET /api/labels/export?wallet_id=` (triggers download) |
| `importLabels` | `POST /api/labels/import?wallet_id=` (multipart/form-data) |

---

## Build

```bash
cd web && npm run build
# tsc -b && vite build
# Output: web/dist/
```

TypeScript is checked with `tsc -b` before Vite bundles. The build must pass with zero errors (deprecation hints in the IDE are not build errors).
