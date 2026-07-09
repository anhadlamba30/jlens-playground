import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { renderAll, renderChatAll } from '../actions.js'

export function renderTokens(elementId = 'tokensPane') {
  const el = $(elementId)
  if (!el) return
  const r = state.result
  if (!r) { el.innerHTML = ''; return }
  el.innerHTML = `<div class="card"><div class="card-title">Tokenized prompt</div><div class="token-strip">${r.tokens.map(t =>
    `<button class="token-chip ${state.selectedPos === t.index ? 'selected' : ''}" data-pos="${t.index}" title="#${t.index} id ${t.token_id}"><span class="idx">${t.index}</span>${esc(t.text || '∅')}</button>`
  ).join('')}</div></div>`
  const isChat = elementId !== 'tokensPane'
  el.querySelectorAll('.token-chip').forEach(b =>
    b.onclick = () => { state.selectedPos = Number(b.dataset.pos); isChat ? renderChatAll() : renderAll() }
  )
}
