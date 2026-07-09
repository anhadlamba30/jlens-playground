import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'

export function renderComparison(elementId = 'comparisonPane') {
  const el = $(elementId)
  if (!el) return
  if (!state.comparisonResult) { el.innerHTML = ''; return }
  const cr = state.comparisonResult
  const notes = cr.notes || []
  const deltas = cr.region_token_delta || []
  el.innerHTML = `<div class="card"><div class="card-title">Baseline Comparison</div>
    ${notes.map(n => `<p style="font-size:13px;color:var(--text-secondary)">${esc(n)}</p>`).join('')}
    ${deltas.length ? `<div style="overflow:auto;max-height:200px"><table class="agg-table">
      <thead><tr><th>Token</th><th>Primary</th><th>Baseline</th><th>Delta</th></tr></thead>
      <tbody>${deltas.map(d => `<tr><td style="font-weight:600">${esc(d.token)}</td><td>${d.primary_cells}</td><td>${d.baseline_cells}</td><td style="color:${d.delta > 0 ? 'var(--green)' : 'var(--red)'}">${d.delta > 0 ? '+' : ''}${d.delta}</td></tr>`).join('')}</tbody>
    </table></div>` : '<p style="color:var(--text-muted);font-size:13px">No significant deltas.</p>'}</div>`
}
