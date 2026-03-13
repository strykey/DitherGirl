const App = (() => {
  let debounceTimer = null;
  let hasImage = false;

  async function init() {
    // forward console output to backend terminal for full visibility
    ['log','info','warn','error','debug'].forEach(level => {
      const orig = console[level];
      console[level] = function(...args) {
        API.jsLog(level + ': ' + args.map(a => (typeof a==='string'?a:JSON.stringify(a))).join(' '));
        orig.apply(console, args);
      };
    });
    // global error catcher to diagnose stuck status
    window.onerror = function(message, source, lineno, colno, err) {
      console.error('Uncaught error', message, source, lineno, colno, err);
      setStatus('error', 'JavaScript error');
      toast('JS error occurred, see console', 'error');
    };

    Canvas.init();

    try {
      await Pipeline.init(() => scheduleApply());
      await Panels.init(() => scheduleApply());
    } catch (err) {
      console.error('initialization failed', err);
      toast('Backend API not available – run via the Python launcher', 'error');
      setStatus('error', 'No backend');
      return;
    }

    bindGlobal();
    bindDrop();
    bindExport();
  }

  function bindGlobal() {
    document.getElementById('btn-open-image').addEventListener('click', openFilePicker);

    async function openFilePicker() {
      const path = await API.call('open_file_dialog');
      if (path) loadImageFromPath(path);
    }

    document.querySelectorAll('.preview-mode-btn').forEach(btn => {
      btn.addEventListener('click', () => Canvas.setMode(btn.dataset.mode));
    });

    document.getElementById('btn-save-preset').addEventListener('click', () => Panels.saveCurrentPreset());
  }

  function bindDrop() {
    const dropZone = document.getElementById('drop-zone');
    const canvasArea = document.getElementById('canvas-area');

    [dropZone, canvasArea].forEach(el => {
      el.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
      });
      el.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
      });
      el.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (!file) return;
        loadImageFromFile(file);
      });
    });

    dropZone.addEventListener('click', () => {
      document.getElementById('btn-open-image').click();
    });
  }

  function bindExport() {
    document.getElementById('btn-export').addEventListener('click', async () => {
      const input = document.createElement('input');
      input.type = 'file';
      input.nwsaveas = 'dithered.png';
      input.accept = 'image/*';

      const fmt = document.getElementById('export-format').value;
      const ext = fmt === 'jpeg' ? 'jpg' : fmt;
      const name = `dithered.${ext}`;

      const path = prompt(`Save path (filename):`, name);
      if (!path) return;

      setStatus('working', 'Exporting...');
      const settings = {
        ...Panels.getSettings(),
        format: fmt.toUpperCase(),
        quality: parseInt(document.getElementById('export-quality').value),
        export_scale: parseInt(document.getElementById('export-scale').value),
      };

      const res = await API.exportImage(path, settings);
      if (res.ok) {
        setStatus('ready', 'Ready');
        toast('Image exported', 'success');
      } else {
        setStatus('error', 'Export failed');
        toast(res.error || 'Export failed', 'error');
      }
    });
  }

  function loadImageFromFile(file) {
    console.time('loadImageFromFile');
    // if we have a native path we can call the backend directly; otherwise we
    // read via FileReader and send base64.
    if (file.path) {
      setStatus('working', 'Loading image from disk...');
      API.loadImage(file.path)
        .then(res => {
          console.timeEnd('loadImageFromFile');
          console.log('API.loadImage result', res);
          handleImageLoaded(res);
        })
        .catch(err => {
          console.timeEnd('loadImageFromFile');
          setStatus('error', 'Failed to load');
          console.error('loadImage error', err);
          if (err && err.message && err.message.includes('pywebview')) {
            toast('Backend API not available – run via the Python launcher', 'error');
          } else {
            toast('Failed to load image', 'error');
          }
        });
      return;
    }

    const reader = new FileReader();
    reader.onload = async e => {
      setStatus('working', 'Decoding image...');
      try {
        const res = await API.call('load_image_base64', e.target.result, file.name);
        console.timeEnd('loadImageFromFile');
        handleImageLoaded(res);
      } catch (err) {
        console.timeEnd('loadImageFromFile');
        setStatus('error', 'Failed to load');
        console.error('load_image_base64 failed', err);
        toast('Failed to load image', 'error');
      }
    };
    reader.readAsDataURL(file);
  }

  async function loadImageFromPath(path) {
    console.time('loadImageFromPath');
    setStatus('working', 'Loading image...');
    try {
      const res = await API.loadImage(path);
      console.log('API.loadImage result', res);
      console.timeEnd('loadImageFromPath');
      handleImageLoaded(res);
    } catch (err) {
      console.timeEnd('loadImageFromPath');
      setStatus('error', 'Failed to load');
      console.error('loadImage failed', err);
      if (err && err.message && err.message.includes('pywebview')) {
        toast('Backend API not available – run via the Python launcher', 'error');
      } else {
        toast('Failed to load image', 'error');
      }
    }
  }

  async function handleImageLoaded(res) {
    console.log('handleImageLoaded', res);
    if (!res.ok) {
      setStatus('error', res.error || 'Failed to load');
      toast(res.error || 'Failed to load image', 'error');
      return;
    }

    // preview should always be provided now
    if (res.preview) {
      Canvas.setOriginal(res.preview);
    }
    hasImage = true;

    document.getElementById('image-thumb-wrap').classList.add('visible');
    document.getElementById('image-thumb').src = res.preview;
    document.getElementById('image-filename').textContent = res.filename;
    document.getElementById('image-dimensions').textContent = `${res.width}×${res.height}`;

    document.getElementById('status-dims').style.display = 'flex';
    document.getElementById('status-size').textContent = `${res.width} × ${res.height}`;

    document.getElementById('btn-save-preset').disabled = false;
    document.getElementById('btn-export').disabled = false;

    setStatus('working', 'Applying dither...');
    await applyDither();
  }

  function scheduleApply() {
    if (!hasImage) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyDither, 320);
  }

  async function applyDither() {
    if (!hasImage) return;
    console.time('applyDither');
    setStatus('working', 'Processing...');
    try {
      const settings = Panels.getSettings();
      const res = await API.applyDither(settings);
      console.timeEnd('applyDither');
      if (res.ok) {
        Canvas.setResult(res.image);
        setStatus('ready', 'Ready');
      } else {
        setStatus('error', res.error || 'Processing failed');
        toast(res.error || 'Dither failed', 'error');
      }
    } catch (err) {
      console.timeEnd('applyDither');
      console.error('applyDither exception', err);
      setStatus('error', 'Processing error');
      toast('Processing error', 'error');
    }
  }

  function setStatus(type, text) {
    const dot  = document.getElementById('status-dot');
    const span = document.getElementById('status-text');
    dot.className  = `status-dot ${type}`;
    span.textContent = text;
  }

  let toastTimer = null;
  function toast(msg, type = '') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast ${type} show`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
  }

  return { init, setStatus, toast };
})();

document.addEventListener('DOMContentLoaded', () => App.init());
