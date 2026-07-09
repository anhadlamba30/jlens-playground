import { state } from '../state.js'

export function getFilteredLayers() {
  const r = state.result
  if (!r) return []
  const all = r.layers
  const n = all.length
  let filtered
  switch (state.layerView) {
    case 'early': filtered = all.slice(0, Math.ceil(n * 0.25)); break
    case 'middle': filtered = all.slice(Math.ceil(n * 0.25), Math.ceil(n * 0.75)); break
    case 'late': filtered = all.slice(Math.ceil(n * 0.75)); break
    default: filtered = all; break
  }
  if (state.layerStep > 1) filtered = filtered.filter((_, i) => i % state.layerStep === 0)
  return filtered
}

export function getFilteredPositions() {
  const r = state.result
  if (!r) return []
  const all = r.positions
  switch (state.positionView) {
    case 'selected3':
      return all.filter(p => Math.abs(p - state.selectedPos) <= 3)
    case 'selected5':
      return all.filter(p => Math.abs(p - state.selectedPos) <= 5)
    default:
      return all
  }
}
