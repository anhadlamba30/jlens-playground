import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { TEMPLATES } from '../templates.js'
import { analyze, renderAll, diagnostics, validateCurrentConfig, handleExport, handleImport, setActiveTab } from '../actions.js'

export function bind() {
  document.querySelectorAll('.topbar-tab').forEach(b =>
    b.onclick = () => setActiveTab(b.dataset.tab)
  )

  const pane = $('controlsPane')
  if (!pane) return
  pane.innerHTML = controlsHTML()
  bindControls()
}

function controlsHTML() {
  return `
    <div class="card">
      <div class="card-title">Model</div>
      <div class="fld" style="margin-bottom:8px">
        <span>Config</span>
        <select id="modelSelect"></select>
      </div>
      <div class="row row-wrap" style="margin-bottom:8px">
        <div class="fld" style="width:80px">
          <span>Top-K</span>
          <input id="topK" type="number" min="1" max="50" value="${state.topK}">
        </div>
        <div class="fld" style="width:90px">
          <span>Max pos</span>
          <input id="maxPositions" type="number" min="1" max="256" value="${state.maxPositions}">
        </div>
        <label class="fld fld-row" style="gap:6px;cursor:pointer">
          <input id="forceDemo" type="checkbox" ${state.forceDemo ? 'checked' : ''}>
          <span style="text-transform:none;letter-spacing:0;color:var(--text-secondary)">Demo</span>
        </label>
      </div>
      <div class="card-title" style="margin-top:4px">Prompt</div>
      <div class="fld" style="margin-bottom:8px">
        <span>Template</span>
        <select id="templateSelect"></select>
      </div>
      <textarea id="prompt" style="min-height:72px" placeholder="Enter a prompt…"></textarea>
      <div class="row" style="margin-top:8px">
        <input type="text" id="baselinePrompt" placeholder="Baseline prompt (optional)" style="flex:1;font-size:12px;padding:6px 10px">
        <label class="fld fld-row" style="gap:4px;cursor:pointer;flex-shrink:0">
          <input id="enableComparison" type="checkbox" ${state.enableComparison ? 'checked' : ''}>
          <span style="text-transform:none;letter-spacing:0;font-size:11px;color:var(--text-secondary)">Compare</span>
        </label>
      </div>
      <div class="row" style="margin-top:10px">
        <button id="analyzeBtn" class="btn btn-primary grow">Analyze</button>
        <button id="validateBtn" class="btn">Validate</button>
      </div>
      <div class="row" style="margin-top:6px">
        <div class="fld" style="width:90px">
          <span>Layer view</span>
          <select id="layerView" style="font-size:12px;padding:5px 8px">
            <option value="all">All</option>
            <option value="early">Early</option>
            <option value="middle">Middle</option>
            <option value="late">Late</option>
          </select>
        </div>
        <div class="fld" style="width:70px">
          <span>Step</span>
          <select id="layerStep" style="font-size:12px;padding:5px 8px">
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="4">4</option>
          </select>
        </div>
        <div class="fld" style="width:110px">
          <span>Position view</span>
          <select id="positionView" style="font-size:12px;padding:5px 8px">
            <option value="all">All</option>
            <option value="selected3">Sel ±3</option>
            <option value="selected5">Sel ±5</option>
          </select>
        </div>
      </div>
      <div class="row row-wrap" style="margin-top:8px">
        <button id="exportBtn" class="btn btn-sm">Export</button>
        <button id="importBtn" class="btn btn-sm">Import</button>
        <button id="clearBtn" class="btn btn-sm">Clear</button>
        <button id="diagBtn" class="btn btn-sm">Diagnostics</button>
      </div>
      <input type="file" id="importFileInput" accept=".json" style="display:none">
    </div>
  `
}

function bindControls() {
  $('prompt').value = state.prompt
  $('baselinePrompt').value = state.baselinePrompt || ''
  $('topK').value = state.topK
  $('maxPositions').value = state.maxPositions
  $('forceDemo').checked = state.forceDemo
  $('enableComparison').checked = state.enableComparison
  $('layerView').value = state.layerView
  $('layerStep').value = state.layerStep
  $('positionView').value = state.positionView

  const ts = $('templateSelect')
  ts.innerHTML = TEMPLATES.map(t => `<option value="${esc(t.value)}">${esc(t.label)}</option>`).join('')
  ts.onchange = e => {
    if (e.target.value) {
      state.prompt = e.target.value
      $('prompt').value = state.prompt
    }
  }

  $('prompt').oninput = e => state.prompt = e.target.value
  $('baselinePrompt').oninput = e => state.baselinePrompt = e.target.value
  $('topK').oninput = e => state.topK = Number(e.target.value)
  $('maxPositions').oninput = e => state.maxPositions = Number(e.target.value)
  $('forceDemo').onchange = e => state.forceDemo = e.target.checked
  $('enableComparison').onchange = e => state.enableComparison = e.target.checked
  $('layerView').onchange = e => { state.layerView = e.target.value; renderAll() }
  $('layerStep').onchange = e => { state.layerStep = Number(e.target.value); renderAll() }
  $('positionView').onchange = e => { state.positionView = e.target.value; renderAll() }

  $('analyzeBtn').onclick = analyze
  $('clearBtn').onclick = () => {
    state.result = null; state.selectedCell = null; state.selectedPos = null
    state.pinned = []; state.comparisonResult = null; renderAll()
  }
  $('diagBtn').onclick = diagnostics
  $('validateBtn').onclick = validateCurrentConfig
  $('exportBtn').onclick = handleExport
  $('importBtn').onclick = () => $('importFileInput').click()
  $('importFileInput').onchange = handleImport
  $('modelSelect').onchange = e => { state.selectedModel = e.target.value; renderModelNote() }
}

export function renderModelSelect() {
  const sel = $('modelSelect')
  if (!sel) return
  sel.innerHTML = state.models.map(m =>
    `<option value="${esc(m.id)}">${esc(m.label)}${m.enabled ? '' : ' (disabled)'}</option>`
  ).join('')
  sel.value = state.selectedModel
  renderModelNote()
}

export function renderStatus() {
  const el = $('status')
  if (!el) return
  el.className = 'topbar-status ' + (state.backendOk ? 'ok' : 'bad')
  el.textContent = state.backendOk ? 'Online' : 'Offline'
}

export function renderModelNote() {
  const el = $('notePane')
  if (!el) return
  const m = state.models.find(x => x.id === state.selectedModel)
  el.innerHTML = m
    ? `<div class="note-text"><b>${esc(m.label)}</b> · <code>${esc(m.model_id)}</code> · <code>${esc(m.lens_path)}</code>${m.notes ? '<br>' + esc(m.notes) : ''}</div>`
    : ''
}

export function renderError() {
  const el = $('errorPane')
  if (!el) return
  if (state.showDiagnostics || !state.error) { el.innerHTML = ''; return }
  el.innerHTML = `<div class="err-box"><b>Error</b><pre>${esc(state.error)}</pre></div>`
}

export function renderAllAnalyze() {
  renderModelSelect()
  renderModelNote()
  renderError()
}
