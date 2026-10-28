/**
 * Main Application Orchestrator & View Router
 */
const App = {
  currentJobId: null,
  pollInterval: null,

  init() {
    console.log('Tenglish Captions AI starting...');

    // Initialize submodules
    CaptionStyles.init();
    VideoUploader.init();
    CaptionEditor.init();
    Exporter.init();

    this.bindGlobalEvents();
    this.checkResumeLastJob();
  },

  async checkResumeLastJob() {
    const lastId = localStorage.getItem('last_completed_job_id') || 'f287fff7';
    if (!lastId) return;
    try {
      const resp = await fetch(`/api/job/${lastId}`);
      if (!resp.ok) return;
      const job = await resp.json();
      if (job && job.status === 'COMPLETED' && job.segments && job.segments.length > 0) {
        let resumeBtn = document.getElementById('resume-editor-btn');
        if (!resumeBtn) {
          const heroActions = document.querySelector('.hero-actions');
          if (heroActions) {
            resumeBtn = document.createElement('button');
            resumeBtn.id = 'resume-editor-btn';
            resumeBtn.className = 'btn btn-primary btn-lg';
            resumeBtn.type = 'button';
            resumeBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            resumeBtn.style.boxShadow = '0 4px 15px rgba(16, 185, 129, 0.4)';
            resumeBtn.innerHTML = `<span>🎬 Open Transcribed Video (${job.filename || 'Video'})</span>`;
            resumeBtn.addEventListener('click', () => {
              CaptionEditor.loadJob(job);
              this.showView('editor');
            });
            heroActions.insertBefore(resumeBtn, heroActions.firstChild);
          }
        }
      }
    } catch (e) {}
  },

  bindGlobalEvents() {
    // Brand click returns to landing view
    const brand = document.getElementById('nav-brand');
    if (brand) {
      brand.addEventListener('click', () => {
        this.showView('landing');
      });
    }

    // Back button in editor view
    const editorBackBtn = document.getElementById('editor-back-btn');
    if (editorBackBtn) {
      editorBackBtn.addEventListener('click', () => {
        if (confirm('Return to upload page? Unsaved changes may be lost.')) {
          this.showView('landing');
        }
      });
    }

    // Cancel in processing view
    const cancelBtn = document.getElementById('cancel-processing-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        this.stopPolling();
        this.showView('landing');
      });
    }
  },

  showView(viewName) {
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));

    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  },

  startJob(jobId, filename) {
    this.currentJobId = jobId;
    this.showView('processing');
    this.resetProcessingUI();
    this.startPolling(jobId);
  },

  resetProcessingUI() {
    const bar = document.getElementById('processing-circle-bar');
    const text = document.getElementById('processing-percent-text');
    const title = document.getElementById('processing-stage-title');
    const subtitle = document.getElementById('processing-stage-subtitle');
    const errBox = document.getElementById('processing-error-box');

    if (bar) bar.style.strokeDashoffset = '264';
    if (text) text.textContent = '5%';
    if (title) title.textContent = 'Processing Video...';
    if (subtitle) subtitle.textContent = 'Extracting audio from video file...';
    if (errBox) errBox.style.display = 'none';

    document.querySelectorAll('.stepper-item').forEach(s => {
      s.className = 'stepper-item';
    });
    const stepExtract = document.getElementById('step-extract');
    if (stepExtract) stepExtract.classList.add('active');
  },

  startPolling(jobId) {
    this.stopPolling();

    this.pollInterval = setInterval(async () => {
      try {
        const resp = await fetch(`/api/status/${jobId}`);
        if (!resp.ok) return;

        const data = await resp.json();
        this.updateProgressUI(data);

        if (data.status === 'COMPLETED') {
          this.stopPolling();
          this.onJobCompleted(jobId);
        } else if (data.status === 'FAILED') {
          this.stopPolling();
          this.onJobFailed(data.error_message || 'Video processing encountered an error.');
        }
      } catch (err) {
        console.warn('Status poll warning:', err);
      }
    }, 1200);
  },

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  },

  updateProgressUI(data) {
    const progress = Math.min(100, Math.max(5, data.progress || 5));
    const bar = document.getElementById('processing-circle-bar');
    const text = document.getElementById('processing-percent-text');
    const title = document.getElementById('processing-stage-title');
    const subtitle = document.getElementById('processing-stage-subtitle');

    // Circular progress stroke calculation (264 is perimeter)
    if (bar) {
      const offset = 264 - (264 * progress) / 100;
      bar.style.strokeDashoffset = offset;
    }

    if (text) text.textContent = `${progress}%`;
    if (subtitle) subtitle.textContent = data.stage_message || 'Processing...';

    // Update steppers
    const sExtract = document.getElementById('step-extract');
    const sTranscribe = document.getElementById('step-transcribe');
    const sTenglish = document.getElementById('step-tenglish');
    const sSync = document.getElementById('step-sync');

    if (data.status === 'EXTRACTING_AUDIO') {
      this.setStepperState(sExtract, 'active');
    } else if (data.status === 'TRANSCRIBING') {
      this.setStepperState(sExtract, 'done');
      this.setStepperState(sTranscribe, 'active');
      if (title) title.textContent = 'Transcribing Telugu Speech...';
    } else if (data.status === 'CONVERTING_TENGLISH') {
      this.setStepperState(sExtract, 'done');
      this.setStepperState(sTranscribe, 'done');
      this.setStepperState(sTenglish, 'active');
      if (title) title.textContent = 'Generating Natural Tenglish...';
    } else if (data.status === 'COMPLETED') {
      this.setStepperState(sExtract, 'done');
      this.setStepperState(sTranscribe, 'done');
      this.setStepperState(sTenglish, 'done');
      this.setStepperState(sSync, 'done');
      if (title) title.textContent = 'Ready for Preview!';
    }
  },

  setStepperState(el, state) {
    if (!el) return;
    el.className = `stepper-item ${state}`;
  },

  async onJobCompleted(jobId) {
    localStorage.setItem('last_completed_job_id', jobId);
    this.showToast('Speech transcribed & converted to Tenglish successfully!');
    try {
      const resp = await fetch(`/api/job/${jobId}`);
      if (!resp.ok) throw new Error('Failed to load job details.');
      const jobData = await resp.json();

      // Transition to Editor
      CaptionEditor.loadJob(jobData);
      this.showView('editor');

    } catch (err) {
      alert(`Error loading job details: ${err.message}`);
      this.showView('landing');
    }
  },

  onJobFailed(errorMsg) {
    const errBox = document.getElementById('processing-error-box');
    const msgEl = document.getElementById('processing-error-msg');
    if (msgEl) msgEl.textContent = errorMsg;
    if (errBox) errBox.style.display = 'flex';
  },

  showToast(message) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-msg');
    if (!toast || !toastMsg) return;

    toastMsg.textContent = message;
    toast.style.display = 'block';

    if (this._toastTimer) clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      toast.style.display = 'none';
    }, 3200);
  }
};

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
