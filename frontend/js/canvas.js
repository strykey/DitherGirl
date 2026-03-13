const Canvas = (() => {
  const state = {
    mode: 'after',
    panX: 0, panY: 0,
    zoom: 1,
    panning: false,
    panStartX: 0, panStartY: 0,
    panOriginX: 0, panOriginY: 0,
    hasImage: false,
    originalSrc: '',
    resultSrc: '',
  };

  const els = {};

  function init() {
    els.area      = document.getElementById('canvas-area');
    els.container = document.getElementById('canvas-container');
    els.empty     = document.getElementById('canvas-empty');
    els.viewport  = document.getElementById('canvas-viewport');
    els.imgMain   = document.getElementById('img-main');
    els.zoomCtrls = document.getElementById('zoom-controls');
    els.zoomLabel = document.getElementById('zoom-label');

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup',   onMouseUp);
    els.area.addEventListener('mousedown', onPanStart);
    els.area.addEventListener('wheel', onWheel, { passive: false });

    document.getElementById('zoom-in').addEventListener('click',  () => adjustZoom(0.25));
    document.getElementById('zoom-out').addEventListener('click', () => adjustZoom(-0.25));
    document.getElementById('zoom-fit').addEventListener('click', resetView);
  }

  function setOriginal(src) {
    state.originalSrc = src;
    state.hasImage    = true;
    if (state.mode === 'before') els.imgMain.src = src;
    showCanvas();
  }

  function setResult(src) {
    state.resultSrc = src;
    if (state.mode === 'after') els.imgMain.src = src;
  }

  function showCanvas() {
    els.empty.style.display    = 'none';
    els.container.style.display = 'block';
    els.zoomCtrls.style.display = 'flex';
    els.area.style.cursor = 'grab';
    resetView();
    applyMode();
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.preview-mode-btn').forEach(b =>
      b.classList.toggle('active', b.dataset.mode === mode)
    );
    applyMode();
  }

  function applyMode() {
    if (state.mode === 'before') {
      els.imgMain.src = state.originalSrc;
    } else {
      els.imgMain.src = state.resultSrc || state.originalSrc;
    }
  }

  function onMouseMove(e) {
    if (!state.panning) return;
    state.panX = state.panOriginX + (e.clientX - state.panStartX);
    state.panY = state.panOriginY + (e.clientY - state.panStartY);
    applyTransform();
  }

  function onMouseUp() {
    state.panning = false;
    if (state.hasImage) els.area.style.cursor = 'grab';
  }

  function onPanStart(e) {
    if (!state.hasImage || e.button !== 0) return;
    state.panning    = true;
    state.panStartX  = e.clientX;
    state.panStartY  = e.clientY;
    state.panOriginX = state.panX;
    state.panOriginY = state.panY;
    els.area.style.cursor = 'grabbing';
  }

  function onWheel(e) {
    if (!state.hasImage) return;
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.88 : 1.12;
    const rect   = els.area.getBoundingClientRect();
    const mx     = e.clientX - rect.left - rect.width  / 2;
    const my     = e.clientY - rect.top  - rect.height / 2;
    const prev   = state.zoom;
    state.zoom   = Math.max(0.1, Math.min(8, state.zoom * factor));
    const r      = state.zoom / prev;
    state.panX   = mx + (state.panX - mx) * r;
    state.panY   = my + (state.panY - my) * r;
    applyTransform();
  }

  function adjustZoom(delta) {
    state.zoom = Math.max(0.1, Math.min(8, state.zoom + delta));
    applyTransform();
  }

  function resetView() {
    state.zoom = 1; state.panX = 0; state.panY = 0;
    applyTransform();
  }

  function applyTransform() {
    els.viewport.style.transform =
      `translate(calc(-50% + ${state.panX}px), calc(-50% + ${state.panY}px)) scale(${state.zoom})`;
    els.zoomLabel.textContent = Math.round(state.zoom * 100) + '%';
  }

  return { init, setOriginal, setResult, setMode };
})();