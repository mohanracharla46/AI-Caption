/**
 * Caption Styles & Presets Manager
 */
const CaptionStyles = {
  // Preset definitions
  presets: {
    pop_big: {
      preset: 'pop_big',
      font_name: 'Montserrat',
      font_size: 30,
      primary_color: '#FFFFFF',
      highlight_color: '#22C55E',
      outline_color: '#000000',
      outline_width: 3.2,
      shadow_offset: 1.8,
      position: 'bottom',
      box_background: false,
      is_reels: true,
      word_zoom: 1.55,
      uppercase: true,
      cssClass: 'style-preset-pop-big'
    },
    word_zoom: {
      preset: 'word_zoom',
      font_name: 'Impact',
      font_size: 28,
      primary_color: '#FFFFFF',
      highlight_color: '#F97316',
      outline_color: '#000000',
      outline_width: 3.0,
      shadow_offset: 1.5,
      position: 'bottom',
      box_background: false,
      is_reels: true,
      word_zoom: 1.45,
      uppercase: true,
      cssClass: 'style-preset-zoom'
    },
    reels_highlight: {
      preset: 'reels_highlight',
      font_name: 'Montserrat',
      font_size: 28,
      primary_color: '#FFFFFF',
      highlight_color: '#A855F7',
      outline_color: '#000000',
      outline_width: 2.5,
      shadow_offset: 1.0,
      position: 'bottom',
      box_background: false,
      is_reels: true,
      word_zoom: 1.25,
      uppercase: false,
      cssClass: 'style-preset-reels'
    },
    bold_yellow: {
      preset: 'bold_yellow',
      font_name: 'Impact',
      font_size: 30,
      primary_color: '#FACC15',
      highlight_color: '#38BDF8',
      outline_color: '#000000',
      outline_width: 3.0,
      shadow_offset: 1.5,
      position: 'bottom',
      box_background: false,
      is_reels: true,
      cssClass: 'style-preset-yellow'
    },
    classic: {
      preset: 'classic',
      font_name: 'Arial',
      font_size: 24,
      primary_color: '#FFFFFF',
      highlight_color: '#A855F7',
      outline_color: '#000000',
      outline_width: 1.5,
      shadow_offset: 1.0,
      position: 'bottom',
      box_background: false,
      is_reels: false,
      cssClass: 'style-preset-classic'
    },
    neon_purple: {
      preset: 'neon_purple',
      font_name: 'Outfit',
      font_size: 28,
      primary_color: '#C084FC',
      highlight_color: '#FFFFFF',
      outline_color: '#000000',
      outline_width: 2.0,
      shadow_offset: 1.0,
      position: 'bottom',
      box_background: false,
      is_reels: true,
      cssClass: 'style-preset-neon'
    },
    minimal_box: {
      preset: 'minimal_box',
      font_name: 'Inter',
      font_size: 22,
      primary_color: '#FFFFFF',
      highlight_color: '#A855F7',
      outline_color: '#000000',
      outline_width: 0.0,
      shadow_offset: 0.0,
      position: 'bottom',
      box_background: true,
      is_reels: false,
      cssClass: 'style-preset-box'
    }
  },

  currentStyle: null,

  init() {
    this.currentStyle = { ...this.presets.pop_big };
    this.bindEvents();
    this.updateControlsUI();
    this.applyToOverlay();
  },

  bindEvents() {
    // Preset buttons click
    document.querySelectorAll('.preset-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        const presetKey = btn.dataset.preset;
        if (this.presets[presetKey]) {
          this.applyPreset(presetKey);
        }
      });
    });

    // Toggle custom options drawer
    const toggleBtn = document.getElementById('toggle-custom-style-btn');
    const drawer = document.getElementById('style-custom-drawer');
    if (toggleBtn && drawer) {
      toggleBtn.addEventListener('click', () => {
        const isHidden = drawer.style.display === 'none';
        drawer.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? 'Custom Options ▴' : 'Custom Options ▾';
      });
    }

    // Custom controls bindings
    const fontSelect = document.getElementById('style-font-name');
    const fontSizeSlider = document.getElementById('style-font-size');
    const fontSizeVal = document.getElementById('font-size-val');
    const primaryColor = document.getElementById('style-primary-color');
    const highlightColor = document.getElementById('style-highlight-color');
    const positionSelect = document.getElementById('style-position');
    const reelsToggle = document.getElementById('style-reels-toggle');
    const boxBgToggle = document.getElementById('style-box-bg-toggle');

    if (fontSelect) fontSelect.addEventListener('change', (e) => {
      this.currentStyle.font_name = e.target.value;
      this.applyToOverlay();
    });

    if (fontSizeSlider) fontSizeSlider.addEventListener('input', (e) => {
      this.currentStyle.font_size = parseInt(e.target.value);
      if (fontSizeVal) fontSizeVal.textContent = e.target.value;
      this.applyToOverlay();
    });

    if (primaryColor) primaryColor.addEventListener('input', (e) => {
      this.currentStyle.primary_color = e.target.value;
      this.applyToOverlay();
    });

    if (highlightColor) highlightColor.addEventListener('input', (e) => {
      this.currentStyle.highlight_color = e.target.value;
      this.applyToOverlay();
    });

    if (positionSelect) positionSelect.addEventListener('change', (e) => {
      this.currentStyle.position = e.target.value;
      this.applyToOverlay();
    });

    if (reelsToggle) reelsToggle.addEventListener('change', (e) => {
      this.currentStyle.is_reels = e.target.checked;
      this.applyToOverlay();
    });

    if (boxBgToggle) boxBgToggle.addEventListener('change', (e) => {
      this.currentStyle.box_background = e.target.checked;
      this.applyToOverlay();
    });

    const zoomSelect = document.getElementById('style-word-zoom');
    if (zoomSelect) zoomSelect.addEventListener('change', (e) => {
      this.currentStyle.word_zoom = parseFloat(e.target.value);
      const valEl = document.getElementById('word-zoom-val');
      if (valEl) valEl.textContent = e.target.value;
      this.applyToOverlay();
    });

    const upperToggle = document.getElementById('style-uppercase-toggle');
    if (upperToggle) upperToggle.addEventListener('change', (e) => {
      this.currentStyle.uppercase = e.target.checked;
      this.applyToOverlay();
    });
  },

  applyPreset(presetKey) {
    const base = this.presets[presetKey];
    if (!base) return;

    this.currentStyle = { ...base };

    // Update active preset button
    document.querySelectorAll('.preset-pill').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.preset === presetKey);
    });

    this.updateControlsUI();
    this.applyToOverlay();
  },

  updateControlsUI() {
    const s = this.currentStyle;
    const fontSelect = document.getElementById('style-font-name');
    const fontSizeSlider = document.getElementById('style-font-size');
    const fontSizeVal = document.getElementById('font-size-val');
    const primaryColor = document.getElementById('style-primary-color');
    const highlightColor = document.getElementById('style-highlight-color');
    const positionSelect = document.getElementById('style-position');
    const reelsToggle = document.getElementById('style-reels-toggle');
    const boxBgToggle = document.getElementById('style-box-bg-toggle');

    if (fontSelect) fontSelect.value = s.font_name;
    if (fontSizeSlider) fontSizeSlider.value = s.font_size;
    if (fontSizeVal) fontSizeVal.textContent = s.font_size;
    if (primaryColor) primaryColor.value = s.primary_color;
    if (highlightColor) highlightColor.value = s.highlight_color;
    if (positionSelect) positionSelect.value = s.position;
    if (reelsToggle) reelsToggle.checked = s.is_reels;
    if (boxBgToggle) boxBgToggle.checked = s.box_background;

    const zoomSelect = document.getElementById('style-word-zoom');
    if (zoomSelect) zoomSelect.value = s.word_zoom ? s.word_zoom.toString() : '1.35';
    const zoomVal = document.getElementById('word-zoom-val');
    if (zoomVal) zoomVal.textContent = s.word_zoom ? s.word_zoom.toString() : '1.35';

    const upperToggle = document.getElementById('style-uppercase-toggle');
    if (upperToggle) upperToggle.checked = !!s.uppercase;
  },

  applyToOverlay() {
    const overlay = document.getElementById('live-caption-overlay');
    const textContent = document.getElementById('caption-text-content');
    if (!overlay || !textContent) return;

    const s = this.currentStyle;

    // Reset preset classes
    overlay.className = 'live-caption-overlay';

    // Position class
    if (s.position === 'middle') overlay.classList.add('pos-middle');
    else if (s.position === 'top') overlay.classList.add('pos-top');
    else overlay.classList.add('pos-bottom');

    // Add preset class if matching
    if (s.cssClass) overlay.classList.add(s.cssClass);

    // Scale font size proportionally if portrait reel
    const wrapper = document.getElementById('video-wrapper');
    const isPortrait = wrapper && wrapper.classList.contains('is-portrait-reel');
    const effectiveFontSize = isPortrait ? Math.min(21, Math.max(15, Math.round(s.font_size * 0.72))) : s.font_size;

    textContent.style.fontFamily = `"${s.font_name}", sans-serif`;
    textContent.style.fontSize = `${effectiveFontSize}px`;
    textContent.style.color = s.primary_color;

    if (s.box_background) {
      textContent.style.background = 'rgba(0, 0, 0, 0.78)';
      textContent.style.backdropFilter = 'blur(6px)';
    } else {
      textContent.style.background = 'transparent';
      textContent.style.backdropFilter = 'none';
    }

    // Set CSS variable for active highlight color & zoom scale
    const activeZoom = s.word_zoom || 1.45;
    document.documentElement.style.setProperty('--word-zoom-scale', activeZoom);
    document.documentElement.style.setProperty('--style-highlight-color', s.highlight_color);

    if (s.uppercase) {
      textContent.style.textTransform = 'uppercase';
    } else {
      textContent.style.textTransform = 'none';
    }
  },

  getStylePayload() {
    return { ...this.currentStyle };
  }
};
