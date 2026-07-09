const API = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8787'

export async function apiGet(path) {
  const r = await fetch(API + path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function apiPost(path, body) {
  const r = await fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!r.ok) {
    let t = await r.text()
    try { t = JSON.parse(t).detail || t } catch {}
    throw new Error(t)
  }
  return r.json()
}

export async function checkHealth() {
  return apiGet('/api/health')
}

export async function fetchModels() {
  return apiGet('/api/models')
}

export async function fetchDiagnostics() {
  return apiGet('/api/diagnostics')
}

export async function analyzePrompt(body) {
  return apiPost('/api/analyze', body)
}

export async function validateConfig(body) {
  return apiPost('/api/validate-config', body)
}

export async function unloadModels() {
  return apiPost('/api/unload', {})
}

export async function saveRun(payload) {
  return apiPost('/api/save-run', payload)
}

export async function chatGenerate(body) {
  return apiPost('/api/chat/generate', body)
}

export async function generateIntervened(body) {
  return apiPost('/api/chat/generate-intervened', body)
}

export async function checkIntervention() {
  return apiPost('/api/chat/check-intervention', {})
}
