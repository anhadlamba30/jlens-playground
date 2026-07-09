import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { renderAll, renderChatAll } from '../actions.js'

export function renderInspector(elementId = 'inspectorPane') {
  const el = $(elementId)
  if (!el) return
  const c = state.selectedCell
  if (!c) {
    el.innerHTML = '<div class="card"><div class="card-title">Cell Inspector</div><p style="color:var(--text-muted);font-size:13px">Click a grid cell to inspect readouts.</p></div>'
    return
  }
  const isChat = elementId !== 'inspectorPane'
  el.innerHTML = `<div class="card"><div class="card-title">Cell Inspector</div>
    <div class="pill">L${c.layer} · P${c.position}</div>
    <div class="tok-list">${c.top.map(t =>
      `<button class="tok-item ${state.pinned.includes(t.token) ? 'pinned' : ''}" data-token="${esc(t.token)}">
        <span class="rk">#${t.rank}</span>
        <span class="tk">${esc(t.token)}</span>
        <span class="sc">${t.score.toFixed(3)}</span>
      </button>`
    ).join('')}</div></div>`
  el.querySelectorAll('.tok-item').forEach(b =>
    b.onclick = () => {
      const tok = b.dataset.token
      state.pinned = state.pinned.includes(tok) ? state.pinned.filter(x => x !== tok) : [...state.pinned, tok]
      isChat ? renderChatAll() : renderAll()
    }
  )
}
