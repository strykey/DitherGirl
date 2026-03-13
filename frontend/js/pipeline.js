const Pipeline = (() => {
  let effectsMeta = {};
  let effects = [];
  let onChange = null;
  let dragSrc = null;

  const DEFAULT_EFFECTS = [
    { id: 'sharpen',              enabled: false },
    { id: 'blur',                 enabled: false },
    { id: 'glow',                 enabled: false },
    { id: 'chromatic_aberration', enabled: false },
    { id: 'jpeg_glitch',          enabled: false },
    { id: 'grain',                enabled: false },
    { id: 'vignette',             enabled: false },
  ];

  async function init(onChangeCb) {
    onChange = onChangeCb;
    effectsMeta = await API.getEffectsMeta();
    effects = DEFAULT_EFFECTS.map(e => ({
      ...e,
      param: effectsMeta[e.id]?.default ?? 1
    }));
    render();
  }

  function render() {
    const container = document.getElementById('effects-list');
    container.innerHTML = '';

    effects.forEach((effect, index) => {
      const meta = effectsMeta[effect.id] || {};
      const item = document.createElement('div');
      item.className = 'effect-item';
      item.draggable = true;
      item.dataset.index = index;

      const min = meta.min ?? 0;
      const max = meta.max ?? 10;
      const pct = ((effect.param - min) / (max - min)) * 100;

      item.innerHTML = `
        <span class="effect-drag-handle">⠿</span>
        <label class="toggle" style="flex-shrink:0">
          <input type="checkbox" data-effect-id="${effect.id}" ${effect.enabled ? 'checked' : ''}>
          <span class="toggle-track"></span>
        </label>
        <span class="effect-name">${meta.label || effect.id}</span>
        <input type="range"
          data-effect-param="${effect.id}"
          min="${min}" max="${max}" step="${(max - min) > 2 ? 1 : 0.1}"
          value="${effect.param}"
          style="width:60px; --progress: ${pct}%"
          ${!effect.enabled ? 'disabled' : ''}
        >
        <span class="effect-param" data-effect-val="${effect.id}">${+effect.param.toFixed(1)}</span>
      `;

      const checkbox = item.querySelector(`[data-effect-id="${effect.id}"]`);
      checkbox.addEventListener('change', e => {
        effects[index].enabled = e.target.checked;
        const rangeEl = item.querySelector(`[data-effect-param="${effect.id}"]`);
        rangeEl.disabled = !e.target.checked;
        triggerChange();
      });

      const rangeEl = item.querySelector(`[data-effect-param="${effect.id}"]`);
      rangeEl.addEventListener('input', e => {
        const val = parseFloat(e.target.value);
        effects[index].param = val;
        const pctNew = ((val - min) / (max - min)) * 100;
        e.target.style.setProperty('--progress', pctNew + '%');
        item.querySelector(`[data-effect-val="${effect.id}"]`).textContent = +val.toFixed(1);
        triggerChange();
      });

      item.addEventListener('dragstart', e => {
        dragSrc = index;
        item.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      item.addEventListener('dragend', () => {
        item.classList.remove('dragging');
        dragSrc = null;
      });
      item.addEventListener('dragover', e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
      });
      item.addEventListener('drop', e => {
        e.preventDefault();
        if (dragSrc !== null && dragSrc !== index) {
          const moved = effects.splice(dragSrc, 1)[0];
          effects.splice(index, 0, moved);
          render();
          triggerChange();
        }
      });

      container.appendChild(item);
    });
  }

  function triggerChange() {
    if (onChange) onChange(getEffects());
  }

  function getEffects() {
    return effects.map(e => ({
      id: e.id,
      enabled: e.enabled,
      param: e.param
    }));
  }

  function setEffects(newEffects) {
    effects = newEffects.map(e => ({
      ...e,
      param: e.param ?? effectsMeta[e.id]?.default ?? 1
    }));
    render();
  }

  return { init, getEffects, setEffects };
})();
