import { boot } from './actions.js'
import { esc } from './utils/escape.js'

window.addEventListener('error', e => {
  document.body.insertAdjacentHTML('afterbegin', `<pre class="fatal">Frontend error: ${esc(e.message)}\n${esc(e.filename)}:${e.lineno}</pre>`)
})

boot()
