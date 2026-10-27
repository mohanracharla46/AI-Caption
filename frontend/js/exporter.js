/**
 * Exporter Component - SRT, VTT, and FFmpeg Subtitle Burner
 */
const Exporter = {
  modal: null,
  burningBox: null,
  readyBox: null,
  progressBar: null,
  pollTimer: null,

  init() {
    this.modal = document.getElementById('export-modal');
    this.burningBox = document.getElementById('export-burning-state');
    this.readyBox = document.getElementById('export-ready-state');
    this.progressBar = document.getElementById('export-progress-bar');

    this.bindEvents();
  },

  bindEvents() {
    // SRT Download
    const srtBtn = document.getElementById('download-srt-btn');
    if (srtBtn) {
      srtBtn.addEventListener('click', () => {
        const jobId = CaptionEditor.currentJobId;
        if (!jobId) return;
        window.location.href = `/api/export/${jobId}/srt`;
      });
    }

    // VTT Download
    const vttBtn = document.getElementById('download-vtt-btn');
    if (vttBtn) {
      vttBtn.addEventListener('click', () => {
        const jobId = CaptionEditor.currentJobId;
        if (!jobId) return;
        window.location.href = `/api/export/${jobId}/vtt`;
      });
    }

    // Burn Video Button
    const burnBtn = document.getElementById('burn-video-btn');
    if (burnBtn) {
      burnBtn.addEventListener('click', () => {
        this.startBurnVideo();
      });
    }

    // Close Modal
    const closeBtn = document.getElementById('close-export-modal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.closeModal();
      });
    }
  },

  async startBurnVideo() {
    const jobId = CaptionEditor.currentJobId;
    if (!jobId) return;

    // First save any unsaved segment changes
    await CaptionEditor.saveSegmentsToServer();

    // Show modal in burning state
    this.modal.style.display = 'flex';
    this.burningBox.style.display = 'block';
    this.readyBox.style.display = 'none';
    if (this.progressBar) this.progressBar.style.width = '20%';

    try {
      const stylePayload = CaptionStyles.getStylePayload();

      const resp = await fetch(`/api/export/${jobId}/burn-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          style: stylePayload,
          segments: CaptionEditor.segments
        })
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to start video rendering.');
      }

      // Start polling for completion
      this.pollBurnStatus(jobId);

    } catch (err) {
      alert(`Burning failed: ${err.message}`);
      this.closeModal();
    }
  },

  pollBurnStatus(jobId) {
    if (this.pollTimer) clearInterval(this.pollTimer);

    let checkCount = 0;

    this.pollTimer = setInterval(async () => {
      checkCount++;
      try {
        const resp = await fetch(`/api/export/${jobId}/burn-status`);
        if (!resp.ok) return;

        const data = await resp.json();

        // Animate progress bar
        const simulatedProg = Math.min(95, 20 + checkCount * 12);
        if (this.progressBar) this.progressBar.style.width = `${simulatedProg}%`;

        if (data.is_ready && data.download_url) {
          clearInterval(this.pollTimer);
          this.onBurnComplete(data.download_url);
        } else if (data.burn_status === 'FAILED') {
          clearInterval(this.pollTimer);
          alert('Video burning failed. Check terminal for FFmpeg logs.');
          this.closeModal();
        }
      } catch (err) {
        console.warn('Poll error:', err);
      }
    }, 1500);
  },

  onBurnComplete(downloadUrl) {
    if (this.progressBar) this.progressBar.style.width = '100%';
    setTimeout(() => {
      this.burningBox.style.display = 'none';
      this.readyBox.style.display = 'block';

      const videoPreview = document.getElementById('exported-video-preview');
      const downloadBtn = document.getElementById('download-exported-video-btn');

      if (videoPreview) {
        videoPreview.src = downloadUrl + `?t=${Date.now()}`;
        videoPreview.load();
      }

      if (downloadBtn) {
        downloadBtn.href = downloadUrl;
      }

      App.showToast('Captioned video encoded successfully!');
    }, 600);
  },

  closeModal() {
    if (this.pollTimer) clearInterval(this.pollTimer);
    if (this.modal) this.modal.style.display = 'none';
    const videoPreview = document.getElementById('exported-video-preview');
    if (videoPreview) videoPreview.pause();
  }
};
