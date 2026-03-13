const API = {
  _ready: false,
  _queue: [],
  // proxy to send JS log lines to the backend so they appear in the Python terminal
  jsLog: async function(...args) {
    try {
      await this.call('js_log', args.map(a => typeof a === 'string' ? a : JSON.stringify(a)));
    } catch (e) {
      // ignore
    }
  },

  init() {
    // initialize connection to python API; in a normal browser we never
    // receive the `pywebviewready` event, so avoid hanging forever by
    // rejecting after a short timeout.
    return new Promise((resolve, reject) => {
      if (window.pywebview && window.pywebview.api) {
        this._ready = true;
        resolve();
        return;
      }

      const onReady = () => {
        this._ready = true;
        cleanup();
        resolve();
      };
      const cleanup = () => {
        window.removeEventListener('pywebviewready', onReady);
        clearTimeout(timer);
      };

      window.addEventListener('pywebviewready', onReady);

      const timer = setTimeout(() => {
        cleanup();
        reject(new Error('pywebview API not available'));
      }, 2000);
    });
  },

  async call(method, ...args) {
    try {
      await this.init();
    } catch (err) {
      return Promise.reject(err);
    }
    if (!this._ready || !window.pywebview || !window.pywebview.api) {
      return Promise.reject(new Error('backend API not ready'));
    }
    return window.pywebview.api[method](...args);
  },

  loadImage: path => API.call('load_image', path),
  applyDither: settings => API.call('apply_dither', settings),
  exportImage: (path, settings) => API.call('export_image', path, settings),
  getPalettes: () => API.call('get_palettes'),
  loadPalette: path => API.call('load_palette', path),
  extractPalette: n => API.call('extract_palette', n),
  getAlgorithms: () => API.call('get_algorithms'),
  getEffectsMeta: () => API.call('get_effects_meta'),
  getPresets: () => API.call('get_presets'),
  savePreset: (name, settings) => API.call('save_preset', name, settings),
  loadPreset: id => API.call('load_preset', id),
  deletePreset: id => API.call('delete_preset', id),
};
