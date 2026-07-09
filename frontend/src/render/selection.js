import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'

export function renderSelection(elementId = 'selectionPane') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!r) { el.innerHTML = ''; return }
  const tok = r.tokens.find(t => t.index === state.selectedPos)
  const cell = state.selectedCell
  const cellTop = cell?.top?.slice(0, 5).map(t => t.token) || []
  el.innerHTML = `<div class="sel-info">
    <div><b>Token:</b> pos ${state.selectedPos} · ${esc(tok ? tok.text : '—')}</div>
    <div><b>Cell:</b>${cell ? ` L${cell.layer} · P${cell.position}` : ' —'}</div>
    ${cell ? `<div><b>Top:</b> ${cellTop.map(t => esc(t)).join(', ')}</div>` : ''}
  </div>`
}
