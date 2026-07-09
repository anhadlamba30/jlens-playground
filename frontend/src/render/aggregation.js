import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { getFilteredLayers, getFilteredPositions } from '../utils/filters.js'

const BAR_COLORS = [
  '#0f172a', '#131b3c', '#172050', '#1c2566', '#212b7e',
  '#293198', '#3237b3', '#3d3ecf', '#4a45ec', '#5a4dff',
]

function computeAggregation(cells, allLayers) {
  const tokenMap = {}
  for (const cell of cells) {
    if (!cell.top) continue
    for (const t of cell.top) {
      if (!tokenMap[t.token]) {
        tokenMap[t.token] = {
          token: t.token, cellCount: 0,
          layerCounts: {},
        }
        for (const layer of allLayers) tokenMap[t.token].layerCounts[layer] = 0
      }
      const e = tokenMap[t.token]
      e.cellCount++
      if (e.layerCounts[cell.layer] !== undefined) e.layerCounts[cell.layer]++
    }
  }
  const entries = Object.values(tokenMap).map(e => ({
    token: e.token,
    cellCount: e.cellCount,
    layerCounts: e.layerCounts,
  })).sort((a, b) => b.cellCount - a.cellCount).slice(0, 30)

  let maxCount = 0
  for (const e of entries) {
    for (const layer of allLayers) {
      maxCount = Math.max(maxCount, e.layerCounts[layer] || 0)
    }
  }
  const range = maxCount || 1

  return { entries, range }
}

export function renderAggregation(elementId = 'aggregationPane') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!r) { el.innerHTML = ''; return }
  const layers = getFilteredLayers()
  const positions = getFilteredPositions()
  const cells = r.cells.filter(c => layers.includes(c.layer) && positions.includes(c.position))
  const { entries, range } = computeAggregation(cells, layers)
  if (entries.length === 0) {
    el.innerHTML = `<div class="card"><div class="card-title">Top Concepts</div><p style="color:var(--text-muted);font-size:13px">No data for current filters.</p></div>`
    return
  }
  el.innerHTML = `<div class="card"><div class="card-title">Top Concepts</div>
    <div style="overflow:auto;max-height:280px"><table class="agg-table">
      <thead><tr><th>Token</th><th>Count</th><th>Layer Distribution</th></tr></thead>
      <tbody>${entries.map(e => {
    const barHtml = layers.map(layer => {
      const count = e.layerCounts[layer] || 0
      const idx = Math.min(BAR_COLORS.length - 1, Math.floor((count / range) * (BAR_COLORS.length - 1)))
      return `<div class="agg-bar-block" style="background:${BAR_COLORS[idx]}" data-tooltip="Layer ${layer}: ${count}"></div>`
    }).join('')
    return `<tr><td style="font-weight:600">${esc(e.token)}</td><td>${e.cellCount}</td><td><div class="agg-bar">${barHtml}</div></td></tr>`
  }).join('')}</tbody>
    </table></div></div>`
}
