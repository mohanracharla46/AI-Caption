/**
 * Video Uploader & Validation Controller
 */
const VideoUploader = {
  selectedFile: null,
  dropzone: null,
  fileInput: null,
  startBtn: null,
  errorBanner: null,
  errorMsg: null,
  previewStrip: null,

  init() {
    this.dropzone = document.getElementById('dropzone');
    this.fileInput = document.getElementById('video-file-input');
    this.startBtn = document.getElementById('start-transcribe-btn');
    this.errorBanner = document.getElementById('upload-error-banner');
    this.errorMsg = document.getElementById('upload-error-msg');
    this.previewStrip = document.getElementById('file-preview-strip');

    this.bindEvents();
  },

  bindEvents() {
    if (!this.dropzone) return;

    // Click to open file picker
    this.dropzone.addEventListener('click', (e) => {
      if (e.target.closest('#remove-file-btn')) return;
      this.fileInput.click();
    });

    // File input changed
    this.fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        this.handleFileSelected(e.target.files[0]);
      }
    });

    // Drag and drop events
    ['dragenter', 'dragover'].forEach(name => {
      this.dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.add('drag-active');
      });
    });

    ['dragleave', 'drop'].forEach(name => {
      this.dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.remove('drag-active');
      });
    });

    this.dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files[0]) {
        this.handleFileSelected(dt.files[0]);
      }
    });

    // Remove file button
    const removeBtn = document.getElementById('remove-file-btn');
    if (removeBtn) {
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearFile();
      });
    }

    // Start transcription button
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => {
        this.uploadAndProcess();
      });
    }

    // Sample video buttons (header & hero action)
    const quickSampleBtn = document.getElementById('quick-sample-btn');
    const samplePillBtn = document.getElementById('sample-pill-btn');

    if (quickSampleBtn) quickSampleBtn.addEventListener('click', () => this.loadSampleVideo());
    if (samplePillBtn) samplePillBtn.addEventListener('click', () => this.loadSampleVideo());
  },

  handleFileSelected(file) {
    this.hideError();

    // Validate extension
    const allowed = ['.mp4', '.mov', '.webm', '.mkv', '.avi'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      this.showError(`Unsupported file format "${ext}". Please upload an MP4, MOV, or WebM video.`);
      return;
    }

    // Validate size (500MB max)
    const maxBytes = 500 * 1024 * 1024;
    if (file.size > maxBytes) {
      this.showError(`File is too large (${(file.size / (1024*1024)).toFixed(1)}MB). Limit is 500MB.`);
      return;
    }

    this.selectedFile = file;

    // Update UI strip
    const fileNameEl = document.getElementById('selected-file-name');
    const fileSizeEl = document.getElementById('selected-file-size');
    if (fileNameEl) fileNameEl.textContent = file.name;
    if (fileSizeEl) fileSizeEl.textContent = this.formatFileSize(file.size);

    if (this.previewStrip) this.previewStrip.style.display = 'flex';
    if (this.startBtn) this.startBtn.disabled = false;
  },

  clearFile() {
    this.selectedFile = null;
    this.fileInput.value = '';
    if (this.previewStrip) this.previewStrip.style.display = 'none';
    if (this.startBtn) this.startBtn.disabled = true;
    this.hideError();
  },

  formatFileSize(bytes) {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  },

  showError(msg) {
    if (this.errorMsg) this.errorMsg.textContent = msg;
    if (this.errorBanner) this.errorBanner.style.display = 'flex';
  },

  hideError() {
    if (this.errorBanner) this.errorBanner.style.display = 'none';
  },

  async loadSampleVideo() {
    App.showToast('Loading bundled Telugu sample video...');
    try {
      // In our project samples directory, sample_telugu_video.mp4 is available
      const resp = await fetch('/samples/sample_telugu_video.mp4');
      if (!resp.ok) {
        // If not mounted at root, check direct API or fallback
        throw new Error('Sample video could not be fetched from server.');
      }
      const blob = await resp.blob();
      const sampleFile = new File([blob], 'sample_telugu_video.mp4', { type: 'video/mp4' });
      this.handleFileSelected(sampleFile);
      App.showToast('Sample video loaded! Click "Generate Tenglish Subtitles".');
    } catch (err) {
      // Fallback: create mock blob
      this.showError(`Could not load sample video automatically: ${err.message}. You can upload any MP4 video directly.`);
    }
  },

  async uploadAndProcess() {
    if (!this.selectedFile) return;

    this.hideError();
    this.startBtn.disabled = true;
    this.startBtn.textContent = 'Uploading Video...';

    const modelSelect = document.getElementById('select-whisper-model');
    const langSelect = document.getElementById('select-audio-lang');

    const formData = new FormData();
    formData.append('file', this.selectedFile);
    formData.append('whisper_model', modelSelect ? modelSelect.value : 'base');
    formData.append('language', langSelect ? langSelect.value : 'te');

    try {
      const resp = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${resp.status}`);
      }

      const data = await resp.json();
      // Start processing view and poller in main App controller
      App.startJob(data.job_id, this.selectedFile.name);

    } catch (err) {
      this.showError(`Upload failed: ${err.message}`);
      this.startBtn.disabled = false;
      this.startBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
        Generate Tenglish Subtitles
      `;
    }
  }
};
