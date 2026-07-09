export const color = (score, min, max) => {
  const x = max === min ? 0.5 : (score - min) / (max - min)
  return `hsl(${260 - x * 170} 82% ${88 - x * 32}%)`
}
