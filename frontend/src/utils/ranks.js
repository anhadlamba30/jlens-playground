export function rankAt(cells, layer, pos, token) {
  const c = cells.find(x => x.layer === layer && x.position === pos)
  const f = c?.top.find(x => x.token === token)
  return f ? f.rank : 51
}
