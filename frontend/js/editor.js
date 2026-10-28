/**
 * Video Caption Editor & Real-Time Subtitle Synchronization Controller
 */
const CaptionEditor = {
  video: null,
  captionOverlay: null,
  captionContent: null,
  segmentsList: null,
  currentJobId: null,
  segments: [],
  activeSegmentIndex: -1,
  activeMode: 'tenglish',

  init() {
    this.video = document.getElementById('main-video');
    this.captionOverlay = document.getElementById('live-caption-overlay');
    this.captionContent = document.getElementById('caption-text-content');
    this.segmentsList = document.getElementById('segments-list-container');

    this.bindVideoControls();
    this.bindEditorActions();
    this.bindKeyboardShortcuts();
  },

  loadJob(jobData) {
    this.currentJobId = jobData.job_id;
    this.segments = jobData.segments || [];
    this.activeMode = jobData.caption_mode || 'tenglish';

    // Set video src
    this.video.src = `/api/job/${this.currentJobId}/video`;
    this.video.load();

    // Render first frame and adjust aspect ratio immediately once metadata is ready
    const adjustVideoLayout = () => {
      try {
        if (this.video.currentTime === 0) {
          this.video.currentTime = 0.001;
        }
        const vw = this.video.videoWidth;
        const vh = this.video.videoHeight;
        const wrapper = document.getElementById('video-wrapper');
        if (wrapper && vw && vh) {
          if (vh > vw) {
            // Vertical Reel (e.g. 9:16 portrait)
            wrapper.classList.add('is-portrait-reel');
            wrapper.style.aspectRatio = `${vw} / ${vh}`;
          } else {
            // Landscape / widescreen
            wrapper.classList.remove('is-portrait-reel');
            wrapper.style.aspectRatio = `${vw} / ${vh}`;
          }
          CaptionStyles.applyToOverlay();
        }
      } catch (e) {}
    };

    this.video.addEventListener('loadeddata', adjustVideoLayout);
    this.video.addEventListener('loadedmetadata', adjustVideoLayout);
    this.video.addEventListener('error', () => {
      console.warn('Video element playback warning:', this.video.error);
    }, { once: true });

    // Update file title
    const filenameEl = document.getElementById('editor-filename');
    if (filenameEl) filenameEl.textContent = jobData.filename || 'Video';

    // Update Mode tabs
    this.updateModeTabsUI();

    // Render segments timeline
    this.renderSegments();

    // Apply styles to overlay
    CaptionStyles.applyToOverlay();
  },

  bindVideoControls() {
    if (!this.video) return;

    const playBtn = document.getElementById('btn-play-pause');
    const playIcon = document.getElementById('icon-play');
    const pauseIcon = document.getElementById('icon-pause');
    const replayBtn = document.getElementById('btn-replay-seg');
    const scrubber = document.getElementById('video-scrubber');
    const progressFill = document.getElementById('video-progress-fill');
    const currTimeText = document.getElementById('current-time-text');
    const totalTimeText = document.getElementById('total-time-text');
    const volumeSlider = document.getElementById('volume-slider');
    const muteBtn = document.getElementById('btn-mute');

    // Play / Pause toggle
    const togglePlay = () => {
      if (this.video.paused || this.video.ended) {
        this.video.play();
      } else {
        this.video.pause();
      }
    };

    if (playBtn) playBtn.addEventListener('click', togglePlay);
    this.video.addEventListener('click', togglePlay);

    this.video.addEventListener('play', () => {
      if (playIcon) playIcon.style.display = 'none';
      if (pauseIcon) pauseIcon.style.display = 'block';
    });

    this.video.addEventListener('pause', () => {
      if (playIcon) playIcon.style.display = 'block';
      if (pauseIcon) pauseIcon.style.display = 'none';
    });

    // Time update & caption synchronization
    this.video.addEventListener('timeupdate', () => {
      const cur = this.video.currentTime;
      const dur = this.video.duration || 0;

      // Update text
      if (currTimeText) currTimeText.textContent = this.formatTime(cur);
      if (totalTimeText && dur) totalTimeText.textContent = this.formatTime(dur);

      // Update scrubber
      if (progressFill && dur > 0) {
        progressFill.style.width = `${(cur / dur) * 100}%`;
      }

      // Sync active subtitle
      this.syncCaptionsToTime(cur);
    });

    // Scrubber click
    if (scrubber) {
      scrubber.addEventListener('click', (e) => {
        const rect = scrubber.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        if (this.video.duration) {
          this.video.currentTime = pos * this.video.duration;
        }
      });
    }

    // Replay active segment button
    if (replayBtn) {
      replayBtn.addEventListener('click', () => {
        if (this.activeSegmentIndex >= 0 && this.segments[this.activeSegmentIndex]) {
          const seg = this.segments[this.activeSegmentIndex];
          this.video.currentTime = seg.start;
          this.video.play();
        } else {
          // Just jump back 2s
          this.video.currentTime = Math.max(0, this.video.currentTime - 2);
        }
      });
    }

    // Volume control
    if (volumeSlider) {
      volumeSlider.addEventListener('input', (e) => {
        this.video.volume = parseFloat(e.target.value);
        this.video.muted = false;
      });
    }

    if (muteBtn) {
      muteBtn.addEventListener('click', () => {
        this.video.muted = !this.video.muted;
      });
    }
  },

  bindEditorActions() {
    // Mode tabs (Tenglish, Telugu, English)
    document.querySelectorAll('.mode-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const mode = tab.dataset.mode;
        if (mode && mode !== this.activeMode) {
          this.switchCaptionMode(mode);
        }
      });
    });

    // Gemini Fix / Retranscribe button
    const geminiBtn = document.getElementById('editor-gemini-btn');
    if (geminiBtn) {
      geminiBtn.addEventListener('click', async () => {
        let key = localStorage.getItem('gemini_api_key') || '';
        if (!key) {
          key = prompt('Enter your free Google Gemini API Key (get one free at aistudio.google.com):');
          if (!key || !key.trim()) return;
          localStorage.setItem('gemini_api_key', key.trim());
          const keyInput = document.getElementById('gemini-api-key-input');
          if (keyInput) keyInput.value = key.trim();
        }

        geminiBtn.disabled = true;
        geminiBtn.textContent = '⏳ Gemini Processing...';
        App.showToast('Transcribing audio with Google Gemini for 99% accuracy...');

        try {
          const resp = await fetch(`/api/job/${this.currentJobId}/retranscribe-gemini`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gemini_api_key: key.trim() })
          });

          if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || 'Gemini processing failed.');
          }

          const data = await resp.json();
          this.segments = data.segments || [];
          this.renderSegments();
          App.showToast('✅ Native Telugu & Tenglish captions generated successfully!');
        } catch (err) {
          alert(`Gemini AI Notice: ${err.message}`);
        } finally {
          geminiBtn.disabled = false;
          geminiBtn.textContent = '✨ Gemini Fix';
        }
      });
    }

    // Add segment button
    const addBtn = document.getElementById('add-segment-btn');
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        this.addNewSegment();
      });
    }

    // Save changes button
    const saveBtn = document.getElementById('save-segments-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        this.saveSegmentsToServer();
      });
    }
  },

  bindKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      // Ignore if user is typing in a textarea or input
      if (['TEXTAREA', 'INPUT'].includes(document.activeElement.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        if (this.video.paused) this.video.play();
        else this.video.pause();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        this.video.currentTime = Math.max(0, this.video.currentTime - 2);
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        this.video.currentTime = Math.min(this.video.duration || 0, this.video.currentTime + 2);
      }
    });
  },

  syncCaptionsToTime(currentTime) {
    let matchedIndex = -1;

    for (let i = 0; i < this.segments.length; i++) {
      const seg = this.segments[i];
      if (currentTime >= seg.start && currentTime <= seg.end) {
        matchedIndex = i;
        break;
      }
    }

    // If segment changed
    if (matchedIndex !== this.activeSegmentIndex) {
      this.activeSegmentIndex = matchedIndex;
      this.highlightSegmentCard(matchedIndex);
    }

    // Render subtitle overlay
    if (matchedIndex >= 0) {
      const seg = this.segments[matchedIndex];
      const isReels = CaptionStyles.currentStyle && CaptionStyles.currentStyle.is_reels;

      if (isReels && seg.words && seg.words.length > 0) {
        // Word-level karaoke animation
        const wordsHtml = seg.words.map(w => {
          const wStart = parseFloat(w.start);
          const wEnd = parseFloat(w.end);
          const isActive = (currentTime >= wStart && currentTime <= wEnd);
          const activeClass = isActive ? 'active-word' : '';
          const wordText = w.word || '';
          return `<span class="word-token ${activeClass}">${wordText}</span>`;
        }).join(' ');

        this.captionContent.innerHTML = wordsHtml;
      } else {
        // Standard sentence text
        this.captionContent.textContent = seg.text || '';
      }

      this.captionOverlay.style.opacity = '1';
    } else {
      // Idle / no active caption at this second
      this.captionContent.innerHTML = '';
      this.captionOverlay.style.opacity = '0';
    }
  },

  renderSegments() {
    if (!this.segmentsList) return;
    this.segmentsList.innerHTML = '';

    const totalEl = document.getElementById('segments-total-count');
    if (totalEl) totalEl.textContent = this.segments.length;

    if (this.segments.length === 0) {
      this.segmentsList.innerHTML = `
        <div class="segments-empty-state">
          <p>No subtitle segments detected for this video.</p>
        </div>
      `;
      return;
    }

    this.segments.forEach((seg, idx) => {
      const card = document.createElement('div');
      card.className = 'segment-card';
      card.dataset.index = idx;
      if (idx === this.activeSegmentIndex) card.classList.add('active-segment');

      // Telugu reference hint if available
      const teluguHint = (seg.telugu_text && this.activeMode !== 'telugu')
        ? `<div class="segment-telugu-hint"><span>Telugu:</span> ${this.escapeHtml(seg.telugu_text)}</div>`
        : '';

      card.innerHTML = `
        <div class="segment-header-row">
          <div class="segment-timing-box">
            <input type="text" class="time-input seg-start" value="${this.formatSeconds(seg.start)}" data-index="${idx}" title="Start Time">
            <span class="time-arrow">→</span>
            <input type="text" class="time-input seg-end" value="${this.formatSeconds(seg.end)}" data-index="${idx}" title="End Time">
          </div>
          <div class="segment-card-actions">
            <button class="segment-play-btn" data-index="${idx}" title="Play segment">
              ▶ Play
            </button>
            <button class="segment-del-btn" data-index="${idx}" title="Delete segment">
              &times;
            </button>
          </div>
        </div>
        <textarea class="segment-textarea" data-index="${idx}" rows="2">${this.escapeHtml(seg.text || '')}</textarea>
        ${teluguHint}
      `;

      // Event: jump video on play button click
      card.querySelector('.segment-play-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        this.playSegment(idx);
      });

      // Event: delete segment
      card.querySelector('.segment-del-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteSegment(idx);
      });

      // Event: text change
      const textarea = card.querySelector('.segment-textarea');
      textarea.addEventListener('input', (e) => {
        this.segments[idx].text = e.target.value;
        if (this.activeMode === 'tenglish') this.segments[idx].tenglish_text = e.target.value;
        else if (this.activeMode === 'telugu') this.segments[idx].telugu_text = e.target.value;
        else if (this.activeMode === 'english') this.segments[idx].english_text = e.target.value;
        
        // Immediate sync if current
        if (idx === this.activeSegmentIndex) {
          this.syncCaptionsToTime(this.video.currentTime);
        }
      });

      // Event: timestamp inputs change
      const startIn = card.querySelector('.seg-start');
      const endIn = card.querySelector('.seg-end');

      startIn.addEventListener('change', (e) => {
        const val = this.parseSeconds(e.target.value);
        if (!isNaN(val)) this.segments[idx].start = Math.max(0, val);
      });

      endIn.addEventListener('change', (e) => {
        const val = this.parseSeconds(e.target.value);
        if (!isNaN(val)) this.segments[idx].end = Math.max(this.segments[idx].start + 0.1, val);
      });

      // Clicking card jumps video to start
      card.addEventListener('click', (e) => {
        if (!['INPUT', 'TEXTAREA', 'BUTTON'].includes(e.target.tagName)) {
          this.playSegment(idx);
        }
      });

      this.segmentsList.appendChild(card);
    });
  },

  highlightSegmentCard(index) {
    document.querySelectorAll('.segment-card').forEach((card, idx) => {
      const isActive = idx === index;
      card.classList.toggle('active-segment', isActive);
      if (isActive) {
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  },

  playSegment(index) {
    if (index >= 0 && index < this.segments.length) {
      const seg = this.segments[index];
      this.video.currentTime = seg.start;
      this.video.play();
    }
  },

  addNewSegment() {
    const curTime = this.video ? this.video.currentTime : 0;
    const newSeg = {
      id: this.segments.length + 1,
      start: Math.round(curTime * 10) / 10,
      end: Math.round((curTime + 2.5) * 10) / 10,
      text: 'New subtitle caption',
      tenglish_text: 'New subtitle caption',
      telugu_text: '',
      words: []
    };

    this.segments.push(newSeg);
    this.segments.sort((a, b) => a.start - b.start);
    this.renderSegments();
    App.showToast('New segment added.');
  },

  deleteSegment(index) {
    if (confirm('Delete this subtitle segment?')) {
      this.segments.splice(index, 1);
      this.renderSegments();
      App.showToast('Segment removed.');
    }
  },

  async switchCaptionMode(mode) {
    if (!this.currentJobId) return;

    App.showToast(`Switching to ${mode.toUpperCase()}...`);
    try {
      const resp = await fetch(`/api/job/${this.currentJobId}/switch-mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });

      if (!resp.ok) throw new Error('Failed to switch mode.');

      const data = await resp.json();
      this.activeMode = data.mode;
      this.segments = data.segments;

      this.updateModeTabsUI();
      this.renderSegments();
      this.syncCaptionsToTime(this.video.currentTime);
      App.showToast(`Switched to ${mode} mode.`);
    } catch (err) {
      App.showToast(`Error: ${err.message}`);
    }
  },

  updateModeTabsUI() {
    document.querySelectorAll('.mode-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.mode === this.activeMode);
    });
  },

  async saveSegmentsToServer() {
    if (!this.currentJobId) return;

    try {
      const resp = await fetch(`/api/job/${this.currentJobId}/segments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segments: this.segments })
      });

      if (!resp.ok) throw new Error('Failed to save segments.');
      App.showToast('All caption changes saved successfully!');
    } catch (err) {
      App.showToast(`Save error: ${err.message}`);
    }
  },

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms}`;
  },

  formatSeconds(sec) {
    return (Math.round(sec * 100) / 100).toFixed(2);
  },

  parseSeconds(str) {
    if (str.includes(':')) {
      const parts = str.split(':');
      if (parts.length === 2) {
        return parseFloat(parts[0]) * 60 + parseFloat(parts[1]);
      }
    }
    return parseFloat(str);
  },

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
