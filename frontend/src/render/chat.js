import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { renderTokens } from './tokens.js'
import { renderGrid } from './grid.js'
import { renderInspector } from './inspector.js'
import { renderAggregation } from './aggregation.js'
import { renderHeatmap } from './heatmap.js'
import { renderChart } from './chart.js'
import { renderSelection } from './selection.js'
import { renderChatAll } from '../actions.js'

let _chatAnalysisOpen = true

export function renderChatTab() {
  renderChatHeader()
  renderChatInputArea()
  renderChatTranscript()
  renderChatSidebar()
  setupAnalysisToggle()
  setupAnalysisDrag()
}

function setupAnalysisToggle() {
  const btn = $('chatAnalysisToggle')
  if (!btn) return
  btn.onclick = () => {
    _chatAnalysisOpen = !_chatAnalysisOpen
    const content = $('chatAnalysisContent')
    if (content) content.style.display = _chatAnalysisOpen ? 'flex' : 'none'
    btn.textContent = _chatAnalysisOpen ? '▼ J-Lens Analysis' : '▶ J-Lens Analysis'
  }
}

function setupAnalysisDrag() {
  const drag = $('chatAnalysisDrag')
  const area = $('chatAnalysisArea')
  if (!drag || !area) return

  let startY = 0
  let startH = 0

  const onMove = (e) => {
    const dy = (e.clientY || e.touches?.[0]?.clientY || 0) - startY
    const newH = Math.max(80, startH - dy)
    area.style.height = newH + 'px'
  }

  const onEnd = () => {
    drag.classList.remove('active')
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onEnd)
    document.removeEventListener('touchmove', onMove)
    document.removeEventListener('touchend', onEnd)
  }

  const onStart = (e) => {
    drag.classList.add('active')
    startY = e.clientY || e.touches?.[0]?.clientY || 0
    startH = area.offsetHeight
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onEnd)
    document.addEventListener('touchmove', onMove, { passive: true })
    document.addEventListener('touchend', onEnd)
  }

  drag.addEventListener('mousedown', onStart)
  drag.addEventListener('touchstart', onStart, { passive: true })
}

export function renderChatAnalysis() {
  const area = $('chatAnalysisArea')
  if (!area) return
  if (!state.result) { area.classList.add('hidden'); return }
  area.classList.remove('hidden')
  if (!area.style.height) area.style.height = '300px'
  const content = $('chatAnalysisContent')
  if (!content) return
  content.innerHTML = ''
  const ids = ['chatTokens', 'chatSelection', 'chatGrid', 'chatAgg', 'chatHeatmap', 'chatChart']
  ids.forEach(id => {
    const d = document.createElement('div')
    d.id = id
    content.appendChild(d)
  })
  renderTokens('chatTokens')
  renderSelection('chatSelection')
  renderGrid('chatGrid', 'chat')
  renderAggregation('chatAgg')
  renderHeatmap('chatHeatmap', 'chat')
  renderChart('chatChart')
  const btn = $('chatAnalysisToggle')
  if (btn) {
    content.style.display = _chatAnalysisOpen ? 'flex' : 'none'
    btn.textContent = _chatAnalysisOpen ? '▼ J-Lens Analysis' : '▶ J-Lens Analysis'
  }
}

function renderChatHeader() {
  const el = $('chatHeader')
  if (!el) return
  const c = state.chat
  el.innerHTML = `
    <div class="fld fld-row">
      <span>Model</span>
      <select id="chatModelSelect" style="width:140px"></select>
    </div>
    <div class="fld fld-row"><span>Tokens</span><input id="chatMaxNewTokens" type="number" min="1" max="512" value="${c.maxNewTokens}" style="width:60px"></div>
    <div class="fld fld-row"><span>Temp</span><input id="chatTemperature" type="number" min="0" max="2" step="0.1" value="${c.temperature}" style="width:60px"></div>
    <div class="fld fld-row"><span>Top-P</span><input id="chatTopP" type="number" min="0" max="1" step="0.05" value="${c.topP}" style="width:60px"></div>
    <div class="fld fld-row"><span>Seed</span><input id="chatSeed" type="number" value="${c.seed}" style="width:60px"></div>
    <label class="fld fld-row" style="cursor:pointer;gap:4px"><input id="chatAnalyzeResponse" type="checkbox" ${c.analyzeResponse ? 'checked' : ''}><span style="text-transform:none;letter-spacing:0;font-size:11px">Analyze</span></label>
    <label class="fld fld-row" style="cursor:pointer;gap:4px"><input id="chatTraceGeneration" type="checkbox" ${c.traceGeneration ? 'checked' : ''}><span style="text-transform:none;letter-spacing:0;font-size:11px">Trace</span></label>
  `
  const sel = $('chatModelSelect')
  if (sel) {
    sel.innerHTML = state.models.map(m =>
      `<option value="${esc(m.id)}">${esc(m.label)}${m.enabled ? '' : ' (disabled)'}</option>`
    ).join('')
    sel.value = state.selectedModel
    sel.onchange = e => state.selectedModel = e.target.value
  }
  $('chatMaxNewTokens').oninput = e => state.chat.maxNewTokens = Number(e.target.value)
  $('chatTemperature').oninput = e => state.chat.temperature = Number(e.target.value)
  $('chatTopP').oninput = e => state.chat.topP = Number(e.target.value)
  $('chatSeed').oninput = e => state.chat.seed = Number(e.target.value)
  $('chatAnalyzeResponse').onchange = e => state.chat.analyzeResponse = e.target.checked
  $('chatTraceGeneration').onchange = e => state.chat.traceGeneration = e.target.checked
}

function renderChatInputArea() {
  const el = $('chatInputArea')
  if (!el) return
  el.innerHTML = `
    <input id="chatInput" type="text" placeholder="Type a message…" value="${esc(state.chat.chatInput)}" style="flex:1">
    <button id="chatSendBtn" class="btn btn-primary" ${state.chat.generating ? 'disabled' : ''}>${state.chat.generating ? '…' : 'Send'}</button>
    <button id="chatClearBtn" class="btn">Clear</button>
  `
  $('chatInput').onkeydown = e => { if (e.key === 'Enter') sendChatMessage() }
  $('chatInput').oninput = e => state.chat.chatInput = e.target.value
  $('chatSendBtn').onclick = sendChatMessage
  $('chatClearBtn').onclick = clearChat
}

function renderChatSidebar() {
  const el = $('chatSidebar')
  if (!el) return
  el.innerHTML = `
    <div id="chatIvPanel"></div>
    <div id="chatGenTokens"></div>
    <div id="chatTracePane"></div>
  `
  renderInterventionPanel()
}

function renderInterventionPanel() {
  const container = $('chatIvPanel')
  if (!container) return
  const iv = state.intervention
  if (!iv.enabled) {
    container.innerHTML = `<div class="card">
      <label class="fld fld-row" style="cursor:pointer;gap:6px"><input id="ivEnabled" type="checkbox"><span style="font-size:13px;font-weight:600">Enable Intervention</span></label>
      <div class="iv-warn" style="margin-top:8px">Experimental additive steering. Not guaranteed to match coordinate-swap methods.</div>
    </div>`
    $('ivEnabled').onchange = e => { state.intervention.enabled = e.target.checked; renderInterventionPanel() }
    return
  }
  container.innerHTML = `<div class="card">
    <label class="fld fld-row" style="cursor:pointer;gap:6px;margin-bottom:8px"><input id="ivEnabled2" type="checkbox" checked><span style="font-size:13px;font-weight:600">Intervention</span></label>
    <div class="row row-wrap" style="margin-bottom:6px">
      <div class="fld" style="width:80px"><span>Mode</span><select id="ivMode" style="font-size:12px">
        <option value="add" ${iv.mode === 'add' ? 'selected' : ''}>Add</option>
        <option value="ablate" ${iv.mode === 'ablate' ? 'selected' : ''}>Ablate</option>
        <option value="swap" ${iv.mode === 'swap' ? 'selected' : ''}>Swap</option>
      </select></div>
      ${iv.mode === 'add' || iv.mode === 'ablate' ? `<div class="fld" style="flex:1"><span>Token</span><input id="ivToken" type="text" value="${esc(iv.token)}" placeholder="monkey" style="font-size:12px"></div>` : ''}
      ${iv.mode === 'swap' ? `<div class="fld" style="flex:1"><span>Source</span><input id="ivSourceToken" type="text" value="${esc(iv.sourceToken)}" style="font-size:12px"></div><div class="fld" style="flex:1"><span>Target</span><input id="ivTargetToken" type="text" value="${esc(iv.targetToken)}" style="font-size:12px"></div>` : ''}
    </div>
    <div class="row row-wrap" style="margin-bottom:6px">
      <div class="fld" style="width:60px"><span>α</span><input id="ivAlpha" type="number" min="0" max="10" step="0.5" value="${iv.alpha}" style="font-size:12px"></div>
      <div class="fld" style="width:60px"><span>L-start</span><input id="ivLayerStart" type="number" min="0" max="32" value="${iv.layerStart}" style="font-size:12px"></div>
      <div class="fld" style="width:60px"><span>L-end</span><input id="ivLayerEnd" type="number" min="0" max="32" value="${iv.layerEnd}" style="font-size:12px"></div>
      <div class="fld" style="width:50px"><span>Step</span><input id="ivLayerStep" type="number" min="1" max="8" value="${iv.layerStep}" style="font-size:12px"></div>
    </div>
    <div class="row row-wrap">
      <div class="fld" style="width:90px"><span>Position</span><select id="ivPositionMode" style="font-size:12px">
        <option value="all" ${iv.positionMode === 'all' ? 'selected' : ''}>All</option>
        <option value="last_prompt" ${iv.positionMode === 'last_prompt' ? 'selected' : ''}>Last prompt</option>
        <option value="selected" ${iv.positionMode === 'selected' ? 'selected' : ''}>Selected</option>
      </select></div>
      <label class="fld fld-row" style="cursor:pointer;gap:4px"><input id="ivNormalize" type="checkbox" ${iv.normalizeVector ? 'checked' : ''}><span style="text-transform:none;font-size:11px">Norm</span></label>
    </div>
    <div class="iv-warn" style="margin-top:8px">⚠ Experimental. Effects are model/layer/prompt dependent.</div>
  </div>`
  $('ivEnabled2').onchange = e => { state.intervention.enabled = e.target.checked; renderInterventionPanel() }
  $('ivMode').onchange = e => { state.intervention.mode = e.target.value; renderInterventionPanel() }
  const ivToken = $('ivToken'); if (ivToken) ivToken.oninput = e => state.intervention.token = e.target.value
  const ivSrc = $('ivSourceToken'); if (ivSrc) ivSrc.oninput = e => state.intervention.sourceToken = e.target.value
  const ivTgt = $('ivTargetToken'); if (ivTgt) ivTgt.oninput = e => state.intervention.targetToken = e.target.value
  $('ivAlpha').oninput = e => state.intervention.alpha = Number(e.target.value)
  $('ivLayerStart').oninput = e => state.intervention.layerStart = Number(e.target.value)
  $('ivLayerEnd').oninput = e => state.intervention.layerEnd = Number(e.target.value)
  $('ivLayerStep').oninput = e => state.intervention.layerStep = Number(e.target.value)
  $('ivPositionMode').onchange = e => state.intervention.positionMode = e.target.value
  $('ivNormalize').onchange = e => state.intervention.normalizeVector = e.target.checked
}

export function renderChatTranscript() {
  const container = $('chatMessages')
  if (!container) return
  container.innerHTML = state.chat.messages.map(m =>
    `<div class="msg msg-${m.role}"><b>${esc(m.role)}:</b> ${esc(m.content)}</div>`
  ).join('')
  container.scrollTop = container.scrollHeight
}

function renderChatGenTokens(data) {
  const container = $('chatGenTokens')
  if (!container || !data?.generated_tokens) { if (container) container.innerHTML = ''; return }
  container.innerHTML = `<div class="card"><div class="card-title">Generated Tokens <span style="text-transform:none;letter-spacing:0" class="muted">(click to inspect)</span></div>
    <div class="token-strip">${data.generated_tokens.map(t =>
      `<button class="gen-token" data-gen-index="${t.index}" data-full-position="${t.index}">${esc(t.text)}</button>`
    ).join('')}</div></div>`
  container.querySelectorAll('.gen-token').forEach(el => {
    el.onclick = () => {
      state.chat.selectedGeneratedToken = Number(el.dataset.genIndex)
      const fp = Number(el.dataset.fullPosition)
      if (state.result && state.result.positions) {
        state.selectedPos = state.result.positions.includes(fp) ? fp : 0
        state.selectedCell = null
        renderChatAll()
      }
    }
  })
}

function renderChatTrace(traceData) {
  const container = $('chatTracePane')
  if (!container) { if (container) container.innerHTML = ''; return }
  if (!traceData) { container.innerHTML = ''; return }
  const tokens = traceData.tokens || []
  const layerKeys = tokens.length > 0 && tokens[0].jlens_by_layer
    ? Object.keys(tokens[0].jlens_by_layer).sort((a, b) => Number(a) - Number(b))
    : []
  let html = `<div class="card"><div class="card-title">Generation Trace</div><div class="trace-wrap"><table class="trace-table">
    <thead><tr><th>#</th><th>Token</th><th>Pos</th>${layerKeys.map(lk => `<th>L${lk}</th>`).join('')}</tr></thead><tbody>`
  for (const tok of tokens) {
    html += `<tr><td>${tok.generated_index}</td><td style="font-weight:600">${esc(tok.text)}</td><td>${tok.full_position}</td>`
    for (const lk of layerKeys) {
      const toks = tok.jlens_by_layer?.[lk] || []
      html += `<td>${toks.slice(0, state.chat.topKTrace).map(t => `<span class="trace-chip">${esc(t.token)}</span>`).join(' ') || '—'}</td>`
    }
    html += `</tr>`
  }
  html += `</tbody></table></div></div>`
  container.innerHTML = html
}

async function sendChatMessage() {
  const text = state.chat.chatInput.trim()
  if (!text || state.chat.generating) return
  state.chat.messages.push({ role: 'user', content: text })
  state.chat.chatInput = ''
  state.chat.generating = true
  renderChatTranscript()
  renderChatInputArea()

  try {
    const layers = state.chat.traceLayers
      ? state.chat.traceLayers.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
      : null

    const { chatGenerate } = await import('../api.js')
    let data

    if (state.intervention.enabled && state.intervention.mode !== 'none') {
      const { generateIntervened } = await import('../api.js')
      data = await generateIntervened({
        model_config_id: state.selectedModel,
        messages: state.chat.messages,
        generation: {
          max_new_tokens: state.chat.maxNewTokens,
          temperature: state.chat.temperature,
          top_p: state.chat.topP,
          seed: state.chat.seed,
        },
        intervention: {
          enabled: true,
          mode: state.intervention.mode,
          token: state.intervention.token || null,
          source_token: state.intervention.sourceToken || null,
          target_token: state.intervention.targetToken || null,
          alpha: state.intervention.alpha,
          layer_start: state.intervention.layerStart,
          layer_end: state.intervention.layerEnd,
          layer_step: state.intervention.layerStep,
          position_mode: state.intervention.positionMode,
          normalize_vector: state.intervention.normalizeVector,
        },
        analyze_outputs: state.chat.analyzeResponse,
      })
      state.intervenedResult = data
    } else {
      data = await chatGenerate({
        model_config_id: state.selectedModel,
        messages: state.chat.messages.map(m => ({ role: m.role, content: m.content })),
        max_new_tokens: state.chat.maxNewTokens,
        temperature: state.chat.temperature,
        top_p: state.chat.topP,
        seed: state.chat.seed,
        analyze_response: state.chat.analyzeResponse,
        trace_generation: state.chat.traceGeneration,
        trace_layers: layers,
      })
    }

    state.chat.messages.push({ role: 'assistant', content: data.generated_text })
    renderChatTranscript()
    renderChatGenTokens(data)

    if (data.analysis) {
      state.result = data.analysis
      state.selectedPos = state.result.positions?.[state.result.positions.length - 1] ?? 0
      renderChatAnalysis()
    }
    if (data.trace) renderChatTrace(data.trace)
    if (state.intervenedResult) {
      compareResult = state.intervenedResult
    }
  } catch (e) {
    const errEl = document.createElement('div')
    errEl.className = 'chat-error'
    errEl.textContent = e.message || String(e)
    $('chatMessages')?.appendChild(errEl)
  }
  state.chat.generating = false
  renderChatInputArea()
}

let compareResult = null

function clearChat() {
  state.chat.messages = []
  state.chat.generatedRuns = []
  state.chat.selectedGeneratedToken = null
  state.result = null
  compareResult = null
  state.intervenedResult = null
  $('chatMessages').innerHTML = ''
  $('chatGenTokens').innerHTML = ''
  $('chatTracePane').innerHTML = ''
  const area = $('chatAnalysisArea')
  if (area) area.classList.add('hidden')
  const content = $('chatAnalysisContent')
  if (content) content.innerHTML = ''
}
