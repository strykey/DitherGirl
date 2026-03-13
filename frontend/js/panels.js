const Panels = (() => {
  let palettes = [];
  let currentPalette = null;
  let algorithms = {};
  let onSettingsChange = null;

  async function init(onChangeCb) {
    onSettingsChange = onChangeCb;
    await Promise.all([loadPalettes(), loadAlgorithms()]);
    bindControls();
    loadPresets();
  }

  async function loadPalettes() {
    palettes = await API.getPalettes();
    const select = document.getElementById('palette-select');
    select.innerHTML = '';
    palettes.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.name} (${p.colors.length})`;
      select.appendChild(opt);
    });
    if (palettes.length > 0) selectPaletteById(palettes[0].id);
    select.addEventListener('change', () => selectPaletteById(select.value));
  }

  function selectPaletteById(id) {
    const p = palettes.find(p => p.id === id);
    if (!p) return;
    currentPalette = p;
    renderSwatches(p.colors);
    if (onSettingsChange) onSettingsChange();
  }

  function renderSwatches(colors) {
    const container = document.getElementById('palette-swatches');
    container.innerHTML = '';
    colors.forEach(hex => {
      const sw = document.createElement('div');
      sw.className = 'palette-swatch';
      sw.style.background = hex;
      sw.title = hex;
      container.appendChild(sw);
    });
  }

  async function loadAlgorithms() {
    algorithms = await API.getAlgorithms();
    const select = document.getElementById('algorithm-select');
    select.innerHTML = '';

    const groups = [
      { key: 'error_diffusion', label: 'Error Diffusion' },
      { key: 'ordered',         label: 'Ordered / Bayer' },
      { key: 'modulation',      label: 'Modulation' },
      { key: 'special',         label: 'Special' },
    ];

    groups.forEach(g => {
      const grp = document.createElement('optgroup');
      grp.label = g.label;
      const entries = algorithms[g.key] || {};
      Object.entries(entries).forEach(([id, desc]) => {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = formatAlgoName(id);
        opt.dataset.desc = desc;
        grp.appendChild(opt);
      });
      select.appendChild(grp);
    });

    select.addEventListener('change', () => {
      updateAlgoDescription();
      updateStatusAlgo();
      if (onSettingsChange) onSettingsChange();
    });

    updateAlgoDescription();
    updateStatusAlgo();
  }

  function formatAlgoName(id) {
    return id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
      .replace('Jjn', 'JJN')
      .replace('2x2', '2×2')
      .replace('4x4', '4×4')
      .replace('8x8', '8×8')
      .replace('16x16', '16×16');
  }

  function updateAlgoDescription() {
    const select = document.getElementById('algorithm-select');
    const opt = select.options[select.selectedIndex];
    document.getElementById('algo-description').textContent = opt?.dataset.desc || '';
  }

  function updateStatusAlgo() {
    const select = document.getElementById('algorithm-select');
    const el = document.getElementById('status-algo');
    const wrap = document.getElementById('status-algo-wrap');
    if (el && select.value) {
      el.textContent = formatAlgoName(select.value);
      wrap.style.display = 'flex';
    }
  }

  function bindControls() {
    const sliders = ['depth', 'threshold', 'brightness', 'contrast', 'scale'];
    sliders.forEach(id => {
      const slider = document.getElementById(`slider-${id}`);
      const val    = document.getElementById(`val-${id}`);
      slider.addEventListener('input', () => {
        let v;
        if (id === 'scale') {
          v = parseFloat(slider.value);
          val.textContent = `×${v.toFixed(2)}`;
        } else {
          v = parseInt(slider.value);
          val.textContent = v;
        }
        updateSliderTrack(slider);
        if (onSettingsChange) onSettingsChange();
      });
      updateSliderTrack(slider);
    });

    document.getElementById('toggle-serpentine').addEventListener('change', () => onSettingsChange && onSettingsChange());
    document.getElementById('toggle-invert').addEventListener('change',     () => onSettingsChange && onSettingsChange());

    document.getElementById('btn-import-palette').addEventListener('click', importPalette);
    document.getElementById('btn-extract-palette').addEventListener('click', extractPalette);

    const extractSlider = document.getElementById('extract-n-colors');
    const extractVal    = document.getElementById('extract-n-val');
    extractSlider.addEventListener('input', () => {
      extractVal.textContent = extractSlider.value;
      updateSliderTrack(extractSlider);
    });
    updateSliderTrack(extractSlider);

    document.getElementById('export-format').addEventListener('change', () => {
      const fmt = document.getElementById('export-format').value;
      document.getElementById('quality-row').style.display =
        (fmt === 'jpeg' || fmt === 'webp') ? 'flex' : 'none';
    });

    const qualitySlider = document.getElementById('export-quality');
    qualitySlider.addEventListener('input', () => {
      document.getElementById('val-quality').textContent = qualitySlider.value;
      updateSliderTrack(qualitySlider);
    });
    updateSliderTrack(qualitySlider);
  }

  function updateSliderTrack(slider) {
    const min = parseFloat(slider.min);
    const max = parseFloat(slider.max);
    const val = parseFloat(slider.value);
    const pct = ((val - min) / (max - min)) * 100;
    slider.style.setProperty('--progress', pct + '%');
  }

  async function importPalette() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,.pal';
    input.onchange = async () => {
      if (!input.files[0]) return;
      const path = input.files[0].path || input.files[0].name;
      const res = await API.loadPalette(path);
      if (res.ok) {
        const p = { ...res.palette, id: `custom_${Date.now()}` };
        palettes.push(p);
        const select = document.getElementById('palette-select');
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.name} (${p.colors.length})`;
        select.appendChild(opt);
        select.value = p.id;
        selectPaletteById(p.id);
        App.toast(`Loaded: ${p.name}`, 'success');
      } else {
        App.toast('Failed to load palette', 'error');
      }
    };
    input.click();
  }

  async function extractPalette() {
    const n = parseInt(document.getElementById('extract-n-colors').value);
    App.setStatus('working', 'Extracting palette...');
    const res = await API.extractPalette(n);
    if (res.ok) {
      const p = {
        id: `extracted_${Date.now()}`,
        name: `Extracted (${n})`,
        colors: res.colors,
        rgb: res.rgb
      };
      palettes.push(p);
      currentPalette = p;
      const select = document.getElementById('palette-select');
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      select.appendChild(opt);
      select.value = p.id;
      renderSwatches(p.colors);
      App.setStatus('ready', 'Ready');
      App.toast(`Extracted ${n} colors`, 'success');
      if (onSettingsChange) onSettingsChange();
    } else {
      App.setStatus('ready', 'Ready');
      App.toast('Extraction failed', 'error');
    }
  }

  async function loadPresets() {
    const list = await API.getPresets();
    renderPresets(list);
  }

  function renderPresets(list) {
    const container = document.getElementById('preset-list');
    container.innerHTML = '';
    if (list.length === 0) {
      container.innerHTML = `<div style="padding:8px 2px; font-family:var(--font-mono); font-size:10px; color:var(--text-muted)">No presets saved</div>`;
      return;
    }
    list.forEach(p => {
      const item = document.createElement('div');
      item.className = 'preset-item';
      item.innerHTML = `
        <span class="preset-item-name">${p.name}</span>
        <div class="preset-item-actions">
          ${p.built_in ? '' : `<button class="btn btn-ghost preset-btn-sm" data-del="${p.id}">✕</button>`}
        </div>
      `;
      item.addEventListener('click', async e => {
        if (e.target.dataset.del) return;
        const res = await API.loadPreset(p.id);
        if (res.ok && res.preset?.settings) {
          applyPreset(res.preset.settings);
          App.toast(`Loaded: ${p.name}`, 'success');
        }
      });
      const delBtn = item.querySelector('[data-del]');
      if (delBtn) {
        delBtn.addEventListener('click', async e => {
          e.stopPropagation();
          await API.deletePreset(p.id);
          loadPresets();
        });
      }
      container.appendChild(item);
    });
  }

  function applyPreset(s) {
    if (s.algorithm) {
      const sel = document.getElementById('algorithm-select');
      sel.value = s.algorithm;
      updateAlgoDescription();
      updateStatusAlgo();
    }
    if (s.palette_id) {
      const palSel = document.getElementById('palette-select');
      palSel.value = s.palette_id;
      selectPaletteById(s.palette_id);
    }
    const setSlider = (id, val) => {
      const el = document.getElementById(`slider-${id}`);
      if (el && val !== undefined) {
        el.value = val;
        el.dispatchEvent(new Event('input'));
      }
    };
    setSlider('depth',      s.depth);
    setSlider('threshold',  s.threshold);
    setSlider('brightness', s.brightness);
    setSlider('contrast',   s.contrast);
    setSlider('scale',      s.scale);

    if (s.serpentine !== undefined) document.getElementById('toggle-serpentine').checked = s.serpentine;
    if (s.invert !== undefined)     document.getElementById('toggle-invert').checked = s.invert;
    if (s.effects)                  Pipeline.setEffects(s.effects);

    if (onSettingsChange) onSettingsChange();
  }

  async function saveCurrentPreset() {
    const name = prompt('Preset name:');
    if (!name) return;
    const settings = getSettings();
    const res = await API.savePreset(name, settings);
    if (res.ok) {
      loadPresets();
      App.toast(`Saved: ${name}`, 'success');
    }
  }

  function getSettings() {
    return {
      algorithm:   document.getElementById('algorithm-select').value,
      palette:     currentPalette,
      depth:       parseInt(document.getElementById('slider-depth').value),
      threshold:   parseInt(document.getElementById('slider-threshold').value),
      brightness:  parseInt(document.getElementById('slider-brightness').value),
      contrast:    parseInt(document.getElementById('slider-contrast').value),
      scale:       parseFloat(document.getElementById('slider-scale').value),
      serpentine:  document.getElementById('toggle-serpentine').checked,
      invert:      document.getElementById('toggle-invert').checked,
      effects:     Pipeline.getEffects(),
    };
  }

  function getCurrentPalette() {
    return currentPalette;
  }

  return { init, getSettings, getCurrentPalette, loadPresets, saveCurrentPreset };
})();
