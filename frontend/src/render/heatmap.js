import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { getFilteredLayers, getFilteredPositions } from '../utils/filters.js'
import { renderAll, renderChatAll } from '../actions.js'

export function renderHeatmap(elementId = 'heatmapPane', prefix = '') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  const hasPinned = state.pinned.length > 0
  if (!(r && hasPinned)) { el.innerHTML = ''; return }

  if (!state.pinned.includes(state.heatmapToken)) state.heatmapToken = state.pinned[0]
  const layers = getFilteredLayers()
  const positions = getFilteredPositions()
  const token = state.heatmapToken
  const cells = r.cells.filter(c => layers.includes(c.layer) && positions.includes(c.position))
  const map = new Map(cells.map(c => [`${c.layer}:${c.position}`, c]))
  const selectId = prefix ? 'chatHeatmapSelect' : 'heatmapSelect'

  let html = `<div class="card"><div class="card-title">Pinned Heatmap</div>
    <div class="row row-wrap" style="margin-bottom:8px">
      <select id="${selectId}" class="heatmap-select">`
  for (const tok of state.pinned) html += `<option value="${esc(tok)}" ${tok === token ? 'selected' : ''}>${esc(tok)}</option>`
  html += `</select><span class="card-title" style="margin:0 0 0 6px;text-transform:none;letter-spacing:0">rank per cell</span></div>
    <div class="grid-wrap" style="max-height:300px"><div class="jlens-grid" style="grid-template-columns:50px repeat(${positions.length}, minmax(44px,1fr))">
    <div class="grid-corner">L/P</div>`
  html += positions.map(p => `<div class="grid-colhead" style="font-size:9px;padding:4px 2px">${p}</div>`).join('')

  const ranks = []
  for (const layer of layers) { for (const pos of positions) { const f = map.get(`${layer}:${pos}`)?.top?.find(t => t.token === token); if (f) ranks.push(f.rank) } }
  const maxRank = ranks.length ? Math.max(...ranks) : state.topK

  for (const layer of layers) {
    html += `<div class="grid-rowhead" style="font-size:9px;padding:4px 6px">${layer}</div>`
    for (const pos of positions) {
      const f = map.get(`${layer}:${pos}`)?.top?.find(t => t.token === token)
      if (f) {
        const pct = (f.rank - 1) / Math.max(maxRank, 1)
        const bg = `color-mix(in srgb, var(--accent) ${100 - pct * 70}%, var(--bg-elevated))`
        html += `<button class="grid-cell" style="background:${bg};font-size:10px;min-width:44px;height:30px" data-layer="${layer}" data-pos="${pos}">#${f.rank}</button>`
      } else {
        html += `<button class="grid-cell" style="background:var(--bg-elevated);min-width:44px;height:30px;cursor:default;color:var(--text-muted)" disabled>—</button>`
      }
    }
  }
  html += `</div></div><p style="font-size:11px;color:var(--text-muted);margin:6px 0 0">Gray = not in top-${state.topK}</p></div>`
  el.innerHTML = html

  const isChat = prefix === 'chat'
  const sel = document.getElementById(selectId)
  if (sel) sel.onchange = e => { state.heatmapToken = e.target.value; isChat ? renderChatAll() : renderAll() }
}