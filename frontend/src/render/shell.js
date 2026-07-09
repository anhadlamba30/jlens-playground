export function renderShell() {
  document.querySelector('#app').innerHTML = `
    <div class="topbar">
      <div class="topbar-brand">
        <div class="topbar-logo">◈</div>
        <span>JLens Playground</span>
      </div>
      <div class="topbar-tabs">
        <button class="topbar-tab active" data-tab="analyze">Prompt Analysis</button>
        <button class="topbar-tab" data-tab="chat">Chat</button>
        <button class="topbar-tab" data-tab="compare">Compare</button>
        <button class="topbar-tab" data-tab="diag">Diagnostics</button>
      </div>
      <div class="topbar-right">
        <div id="status" class="topbar-status bad">Offline</div>
      </div>
    </div>

    <div class="tab-content">
      <!-- Analyze Tab -->
      <div class="tab-pane active" id="pane-analyze">
        <div class="analyze-layout">
          <div class="analyze-sidebar" id="analyzeSidebar">
            <div id="controlsPane"></div>
            <div id="notePane"></div>
            <div id="errorPane"></div>
            <div id="inputEchoPane"></div>
          </div>
          <div class="analyze-main" id="analyzeMain">
            <div id="tokensPane"></div>
            <div id="selectionPane"></div>
            <div id="gridPane"></div>
            <div id="aggregationPane"></div>
            <div id="heatmapPane"></div>
            <div id="chartPane"></div>
            <div id="comparisonPane"></div>
          </div>
          <div class="analyze-inspector" id="analyzeInspector">
            <div id="inspectorPane"></div>
            <div class="card tips-card">
              <div class="card-title">Tips</div>
              <ul class="tips-list">
                <li>Click tokens to focus positions</li>
                <li>Click cells to inspect readouts</li>
                <li>Pin tokens in the inspector</li>
                <li>Try baseline comparison</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Tab -->
      <div class="tab-pane" id="pane-chat">
        <div class="chat-layout">
          <div style="display:flex;flex-direction:column;overflow:hidden;flex:1">
            <div class="chat-header" id="chatHeader"></div>
            <div class="chat-messages" id="chatMessages"></div>
            <div id="chatAnalysisArea" class="hidden" style="flex-shrink:0;overflow-y:auto;padding:0 20px 12px;border-top:1px solid var(--border);min-height:80px">
              <div class="chat-analysis-drag" id="chatAnalysisDrag">
                <div class="chat-analysis-drag-track"></div>
              </div>
              <div style="display:flex;align-items:center;gap:8px;padding:4px 0 8px;position:sticky;top:0;background:var(--bg-base);z-index:1">
                <button id="chatAnalysisToggle" class="btn btn-sm" style="font-size:11px">▼ J-Lens Analysis</button>
              </div>
              <div id="chatAnalysisContent" style="display:flex;flex-direction:column;gap:12px"></div>
            </div>
            <div class="chat-input-area" id="chatInputArea"></div>
          </div>
          <div class="chat-sidebar" id="chatSidebar"></div>
        </div>
      </div>

      <!-- Compare Tab -->
      <div class="tab-pane" id="pane-compare">
        <div class="compare-content" id="compareContent"></div>
      </div>

      <!-- Diagnostics Tab -->
      <div class="tab-pane" id="pane-diag">
        <div class="diag-content" id="diagContent"></div>
      </div>
    </div>`
}
