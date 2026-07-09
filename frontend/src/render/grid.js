import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { getFilteredLayers, getFilteredPositions } from '../utils/filters.js'
import { renderAll, renderChatAll } from '../actions.js'

const CELL_COLORS = [
  '#1e293b',
  '#1e274a', '#1f2655', '#212560', '#24246b',
  '#282376', '#2d2281', '#33218c', '#3a2097',
  '#421fa2',
]

export function renderGrid(elementId = 'gridPane', prefix = '') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!r) {
    el.innerHTML = '<div class="card card-empty">Run an analysis to see the layer × position grid.</div>'
    return
  }
  const layers = getFilteredLayers()
  const positions = getFilteredPositions()
  if (layers.length === 0 || positions.length === 0) {
    el.innerHTML = '<div class="card card-empty">No cells match current filters.</div>'
    return
  }

  const cells = r.cells.filter(c => layers.includes(c.layer) && positions.includes(c.position))
  const scores = cells.map(c => c.top?.[0]?.score ?? 0)
  const min = Math.min(...scores)
  const max = Math.max(...scores)
  const range = max - min || 1
  const map = new Map(cells.map(c => [`${c.layer}:${c.position}`, c]))

  const toggleId = prefix + 'gridToggle'
  const bodyId = prefix + 'gridBody'
  const arrowId = prefix + 'gridArrow'

  let html = `<div class="card">`
  html += `<div class="card-title" style="cursor:pointer" id="${toggleId}"><span id="${arrowId}">▶</span> Layer × Position Grid</div>`
  html += `<div id="${bodyId}" style="display:none"><div class="grid-wrap"><div class="jlens-grid" style="grid-template-columns:60px repeat(${positions.length}, minmax(60px,1fr))">`
  html += `<div class="grid-corner">L/P</div>`
  html += positions.map(p => `<div class="grid-colhead ${state.selectedPos === p ? 'hot' : ''}">${p}</div>`).join('')

  for (const layer of layers) {
    html += `<div class="grid-rowhead">${layer}</div>`
    for (const pos of positions) {
      const c = map.get(`${layer}:${pos}`)
      const top = c?.top?.[0]
      const sel = state.selectedCell && state.selectedCell.layer === layer && state.selectedCell.position === pos
      const pinned = top && state.pinned.includes(top.token)
      if (top) {
        const idx = Math.min(CELL_COLORS.length - 1, Math.floor(((top.score - min) / range) * (CELL_COLORS.length - 1)))
        const bg = CELL_COLORS[idx]
        html += `<button class="grid-cell ${sel ? 'selected' : ''} ${pinned ? 'pinned' : ''}" data-layer="${layer}" data-pos="${pos}" style="background:${bg}"><span class="tok">${esc(top.token)}</span><span class="rk">#${top.rank}</span></button>`
      } else {
        html += `<button class="grid-cell" style="background:var(--bg-elevated);cursor:default" disabled>—</button>`
      }
    }
  }
  html += `</div></div></div></div>`
  el.innerHTML = html

  const toggle = $(toggleId)
  const body = $(bodyId)
  const arrow = $(arrowId)
  if (toggle && body && arrow) {
    toggle.onclick = () => {
      const isOpen = body.style.display !== 'none'
      body.style.display = isOpen ? 'none' : 'block'
      arrow.textContent = isOpen ? '▶' : '▼'
    }
  }

  const isChat = prefix === 'chat'
  el.querySelectorAll('.grid-cell:not([disabled])').forEach(b =>
    b.onclick = () => {
      state.selectedCell = map.get(`${b.dataset.layer}:${b.dataset.pos}`)
      state.selectedPos = Number(b.dataset.pos)
      isChat ? renderChatAll() : renderAll()
    }
  )
}