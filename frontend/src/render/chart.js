import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { rankAt } from '../utils/ranks.js'

export function renderChart(elementId = 'chartPane') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!(r && state.pinned.length)) { el.innerHTML = ''; return }
  const layers = r.layers
  const pos = state.selectedPos ?? r.positions[0]
  const W = 700, H = 220, P = 30
  const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#60a5fa', '#a78bfa']
  const maxRank = Math.max(10, ...state.pinned.flatMap(tok => layers.map(l => rankAt(r.cells, l, pos, tok))))
  const x = i => P + i * ((W - P * 2) / Math.max(1, layers.length - 1))
  const y = rank => P + (rank - 1) * ((H - P * 2) / Math.max(1, maxRank - 1))
  const lines = state.pinned.map((tok, i) =>
    `<polyline points="${layers.map((l, j) => `${x(j)},${y(rankAt(r.cells, l, pos, tok))}`).join(' ')}" fill="none" stroke="${colors[i % colors.length]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`
  ).join('')
  el.innerHTML = `<div class="card"><div class="card-title">Pinned Rank Trajectories · position ${pos}</div>
    <svg class="chart" viewBox="0 0 ${W} ${H}" style="width:100%">
      <line x1="${P}" y1="${P}" x2="${P}" y2="${H - P}" stroke="var(--border)"/>
      <line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" stroke="var(--border)"/>
      ${lines}
      <text x="6" y="${P + 4}" font-size="11" fill="var(--text-muted)">#1</text>
      <text x="6" y="${H - P + 4}" font-size="11" fill="var(--text-muted)">#${maxRank}</text>
    </svg>
    <div class="legend">${state.pinned.map((tok, i) => `<span><b style="background:${colors[i % colors.length]}"></b>${esc(tok)}</span>`).join('')}</div></div>`
}
