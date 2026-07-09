import { $ } from '../dom.js'
import { state } from '../state.js'
import { esc } from '../utils/escape.js'
import { fetchDiagnostics } from '../api.js'
import { renderAll } from '../actions.js'

export async function showDiagnostics() {
  state.showDiagnostics = !state.showDiagnostics
  if (!state.showDiagnostics) { renderAll(); return }
  try {
    state.diagnosticsData = await fetchDiagnostics()
  } catch (e) {
    state.diagnosticsData = { error: e.message }
  }
  renderAll()
}

export function renderDiagnostics() {
  const el = $('diagContent')
  if (!el) return
  if (!state.showDiagnostics || !state.diagnosticsData) { el.innerHTML = ''; return }
  const d = state.diagnosticsData
  el.innerHTML = `<div class="card"><div class="card-title">Diagnostics</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px">
      <div><b>Backend:</b> ${state.backendOk ? 'Online' : 'Offline'}</div>
      <div><b>Python:</b> ${esc(d.python || '—')}</div>
      <div><b>Torch:</b> ${esc(d.torch?.version || '—')}</div>
      <div><b>MPS:</b> ${d.torch?.mps ? 'Available' : 'N/A'}</div>
      <div><b>CUDA:</b> ${d.torch?.cuda ? 'Available' : 'N/A'}</div>
      <div><b>jlens:</b> ${d.jlens?.imported ? 'Imported' : 'Failed: ' + esc(d.jlens?.error || '')}</div>
    </div>
    <div style="margin-top:10px;font-size:13px"><b>Config path:</b> ${esc(d.config_path || '—')}</div>
    <div style="margin-top:6px;font-size:13px"><b>.pt files:</b> ${(d.lens_files || []).map(f => esc(f)).join(', ') || 'None'}</div>
    <div style="margin-top:12px"><button class="btn btn-sm" onclick="navigator.clipboard.writeText(JSON.stringify(${esc(JSON.stringify(d))},null,2))">Copy</button></div></div>`
}
