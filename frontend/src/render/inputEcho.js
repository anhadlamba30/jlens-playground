import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'

export function renderInputEcho(elementId = 'inputEchoPane') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!r || !state.selectedCell) { el.innerHTML = ''; return }
  const tok = r.tokens.find(t => t.index === state.selectedPos)
  if (!tok) { el.innerHTML = ''; return }
  const topTokens = state.selectedCell.top.slice(0, 3).map(t => t.token.toLowerCase().trim())
  const selText = tok.text.toLowerCase().trim()
  if (!selText || !topTokens.some(t => t.includes(selText) || selText.includes(t))) { el.innerHTML = ''; return }
  el.innerHTML = `<div class="err-box" style="border-color:var(--amber-subtle);color:var(--amber);background:var(--amber-subtle)">
    ⚠ Input echo: selected token "${esc(tok.text)}" resembles top readout tokens.</div>`
}
