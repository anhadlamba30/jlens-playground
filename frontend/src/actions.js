import { $ } from './dom.js'
import { state } from './state.js'
import { analyzePrompt, fetchModels, checkHealth, validateConfig, fetchDiagnostics } from './api.js'
import { renderStatus, renderModelSelect, renderModelNote, renderError, bind, renderAllAnalyze } from './render/controls.js'
import { renderTokens } from './render/tokens.js'
import { renderGrid } from './render/grid.js'
import { renderInspector } from './render/inspector.js'
import { renderChart } from './render/chart.js'
import { renderSelection } from './render/selection.js'
import { renderAggregation } from './render/aggregation.js'
import { renderHeatmap } from './render/heatmap.js'
import { renderDiagnostics, showDiagnostics } from './render/diagnostics.js'
import { renderInputEcho } from './render/inputEcho.js'
import { renderComparison } from './render/comparison.js'
import { renderChatTab } from './render/chat.js'

export function renderAll() {
  renderStatus()
  renderAllAnalyze()
  renderTokens()
  renderSelection()
  renderGrid()
  renderAggregation()
  renderInspector()
  renderInputEcho()
  renderChart()
  renderHeatmap()
  renderComparison()
  renderDiagnostics()
}

export function renderChatAll() {}

export function setActiveTab(tab) {
  state.activeTab = tab
  document.querySelectorAll('.topbar-tab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab))
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'))

  const pane = $(`pane-${tab}`)
  if (!pane) return
  pane.classList.add('active')

  if (tab === 'analyze') {
    renderAll()
  } else if (tab === 'chat') {
    renderChatTab()
  } else if (tab === 'compare') {
    state.showDiagnostics = false
    renderAll()
    renderCompareTab()
  } else if (tab === 'diag') {
    if (!state.showDiagnostics) showDiagnostics()
    else { renderAll() }
  }
}

function renderCompareTab() {
  const container = $('compareContent')
  if (!container) return
  const r = state.intervenedResult
  if (!r) {
    container.innerHTML = '<div class="card"><div class="card-title">Clean vs Intervened</div><p style="color:var(--text-muted);font-size:14px">Run a chat with intervention enabled to see comparison here.</p></div>'
    return
  }
  const clean = r.clean || {}
  const intervened = r.intervened || {}
  const diff = r.diff || {}
  const iv = r.intervention || {}
  container.innerHTML = `
    <div class="card-title" style="font-size:14px;text-transform:none;letter-spacing:0;font-weight:700">Clean vs Intervened</div>
    <div class="cmp-grid" style="margin-top:12px">
      <div class="cmp-box clean">
        <div class="cmp-box-label">Clean</div>
        <div class="cmp-text">${esc(clean.generated_text || '—')}</div>
        <div style="margin-top:6px;font-size:12px;color:var(--text-muted)">${(clean.generated_tokens || []).length} tokens</div>
      </div>
      <div class="cmp-box intervened">
        <div class="cmp-box-label">Intervened</div>
        <div class="cmp-text">${esc(intervened.generated_text || '—')}</div>
        <div style="margin-top:6px;font-size:12px;color:var(--text-muted)">${(intervened.generated_tokens || []).length} tokens</div>
      </div>
    </div>
    <div class="card" style="margin-top:12px;display:flex;gap:16px;align-items:center">
      <span style="font-weight:600;font-size:13px">${diff.same_output ? 'Outputs are identical' : 'Outputs differ'}</span>
      <span style="color:var(--text-muted);font-size:12px">Clean: ${diff.clean_length} tokens · Intervened: ${diff.intervened_length} tokens</span>
    </div>
    <div class="iv-warn" style="margin-top:12px">
      <b>Intervention config:</b>
      <pre style="margin:4px 0 0;font-family:var(--font-mono);font-size:11px;white-space:pre-wrap">${esc(JSON.stringify(iv, null, 2))}</pre>
    </div>
    <div class="iv-warn" style="margin-top:8px">⚠ Interventions are experimental. Effects are model-, layer-, prompt-, and lens-dependent.</div>`
}

export async function analyze() {
  state.loading = true
  state.error = ''
  state.result = null
  state.selectedCell = null
  state.selectedPos = null
  state.pinned = []
  state.comparisonResult = null
  renderAll()
  const btn = $('analyzeBtn')
  if (btn) { btn.textContent = '…'; btn.disabled = true }
  try {
    const body = {
      model_config_id: state.selectedModel,
      prompt: state.prompt,
      top_k: state.topK,
      max_positions: state.maxPositions,
      force_demo: state.forceDemo
    }
    if (state.enableComparison && state.baselinePrompt.trim()) {
      body.baseline_prompt = state.baselinePrompt
    }
    const data = await analyzePrompt(body)
    state.result = data
    state.selectedPos = data.positions?.[data.positions.length - 1] ?? 0
    state.selectedCell = data.cells?.[0] ?? null
    if (data.comparison) state.comparisonResult = data.comparison
  } catch (e) {
    state.error = e.message || String(e)
  }
  state.loading = false
  if (btn) { btn.textContent = 'Analyze'; btn.disabled = false }
  renderAll()
}

export async function diagnostics() {
  await showDiagnostics()
  if (state.activeTab === 'diag') {
    renderDiagnostics()
  }
}

export async function validateCurrentConfig() {
  try {
    const result = await validateConfig({ model_config_id: state.selectedModel, deep: true })
    const lines = result.checks.map(c => `${c.ok ? '✓' : '✗'} ${c.name}${c.detail ? ': ' + c.detail : ''}`)
    state.error = `Validation ${result.ok ? 'passed' : 'failed'}:\n` + lines.join('\n')
  } catch (e) {
    state.error = e.message || String(e)
  }
  renderAll()
}

export function handleExport() {
  const data = state.intervenedResult || state.result
  if (!data) return
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'jlens-run.json'; a.click()
  URL.revokeObjectURL(url)
}

export function handleImport(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result)
      state.result = data
      state.selectedPos = data.positions?.[data.positions.length - 1] ?? 0
      state.selectedCell = data.cells?.[0] ?? null
      state.pinned = []
      state.comparisonResult = null
      state.error = ''
      renderAll()
    } catch (err) {
      state.error = 'Failed to import: ' + err.message
      renderAll()
    }
  }
  reader.readAsText(file)
  event.target.value = ''
}

export async function boot() {
  const { renderShell } = await import('./render/shell.js')
  renderShell()
  try {
    await checkHealth()
    state.backendOk = true
  } catch {
    state.backendOk = false
  }
  try {
    state.models = await fetchModels()
    if (state.models[0]) state.selectedModel = state.models[0].id
  } catch (e) {
    state.error = e.message || String(e)
  }
  renderAll()
  bind()
}
