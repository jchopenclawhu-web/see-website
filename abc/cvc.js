// CVC Words — 珊蒂美語 Pre-K progressive unlock
// Loads cvc-words.json, shows one family per week, audio per page intro.

const STORAGE_KEY = 'cvc_settings_v1';
const DEFAULT_PIN = '0000';

// State
let data = null;
let settings = { level: 'prek', max_week: 1 };
let currentWeek = 1;

// DOM
const el = (id) => document.getElementById(id);

// Load settings from localStorage
function loadSettings() {
  try {
    const s = localStorage.getItem(STORAGE_KEY);
    if (s) settings = { ...settings, ...JSON.parse(s) };
  } catch (e) {
    console.warn('Failed to load settings', e);
  }
}
function saveSettings() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch (e) {
    console.warn('Failed to save settings', e);
  }
}

// URL param override
function applyURLParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('level')) settings.level = params.get('level');
  if (params.get('week')) currentWeek = Math.max(1, Math.min(25, parseInt(params.get('week')) || 1));
  if (params.get('max_week')) settings.max_week = Math.max(1, Math.min(25, parseInt(params.get('max_week')) || 1));
}

// Effective max week based on level
function effectiveMaxWeek() {
  if (settings.level === 'prek') return settings.max_week;
  return 25;  // L1, L2 see all
}

// Audio playback
let audio = null;
let playBtn, playIcon, progressFill, progressHandle, timeCurrent, timeTotal, progressTrack;

function initAudio() {
  audio = el('audio');
  playBtn = el('playBtn');
  playIcon = el('playIcon');
  progressFill = el('progressFill');
  progressHandle = el('progressHandle');
  timeCurrent = el('timeCurrent');
  timeTotal = el('timeTotal');
  progressTrack = el('progressTrack');

  playBtn.addEventListener('click', togglePlay);
  audio.addEventListener('timeupdate', updateProgress);
  audio.addEventListener('loadedmetadata', () => {
    timeTotal.textContent = formatTime(audio.duration);
  });
  audio.addEventListener('ended', () => setPlaying(false));

  // Click progress bar to seek
  progressTrack.addEventListener('click', (e) => {
    if (!audio.duration) return;
    const rect = progressTrack.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audio.currentTime = Math.max(0, Math.min(audio.duration, pct * audio.duration));
  });
}

function formatTime(s) {
  if (isNaN(s)) return '0:00';
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

function updateProgress() {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  progressFill.style.width = pct + '%';
  progressHandle.style.left = pct + '%';
  timeCurrent.textContent = formatTime(audio.currentTime);
}

function setPlaying(playing) {
  if (playing) {
    playIcon.textContent = '❚❚';
    playBtn.classList.add('playing');
  } else {
    playIcon.textContent = '▶';
    playBtn.classList.remove('playing');
  }
}

function togglePlay() {
  if (!audio.src) return;
  if (audio.paused) {
    audio.play();
    setPlaying(true);
  } else {
    audio.pause();
    setPlaying(false);
  }
}

// Render current week
function renderWeek() {
  if (!data) return;
  const maxWeek = effectiveMaxWeek();
  currentWeek = Math.max(1, Math.min(maxWeek, currentWeek));
  const page = data.pages.find(p => p.week === currentWeek);
  if (!page) return;

  const isUnlocked = currentWeek <= maxWeek;

  // Header
  el('levelLabel').textContent = settings.level === 'prek' ? 'Pre-K' : settings.level.toUpperCase();
  el('weekLabel').textContent = `Week ${currentWeek} of 25`;
  el('familyBadge').textContent = `-${page.family} family`;
  el('familyTitle').textContent = `Short ${page.vowel} · -${page.family}`;
  el('playerHint').textContent = isUnlocked
    ? 'Tap play to hear this week\'s words'
    : '🔒 Locked — ask your teacher to unlock';

  // Audio
  if (isUnlocked && page.audio_file) {
    audio.src = page.audio_file + '?v=2';
    audio.load();
    el('playBtn').disabled = false;
  } else {
    audio.removeAttribute('src');
    audio.load();
    el('playBtn').disabled = true;
  }

  // Words
  const grid = el('wordGrid');
  grid.innerHTML = '';
  if (!isUnlocked) {
    grid.innerHTML = `<div class="locked-msg"><span class="lock-icon">🔒</span>Week ${currentWeek} is locked.<br>Your teacher hasn't unlocked it yet.</div>`;
  } else {
    page.words.forEach((w, i) => {
      const tile = document.createElement('button');
      tile.className = 'word-tile' + (i === 0 ? ' family-word' : '');
      tile.type = 'button';
      tile.textContent = w;
      tile.addEventListener('click', () => showBigWord(w));
      grid.appendChild(tile);
    });
  }

  // Lock state
  document.querySelector('.player-card').classList.toggle('locked', !isUnlocked);
  document.querySelector('.words-card').classList.toggle('locked', !isUnlocked);

  // Nav buttons
  el('prevBtn').disabled = currentWeek <= 1;
  el('nextBtn').disabled = currentWeek >= maxWeek;
}

// Big word overlay
function showBigWord(word) {
  el('bigWord').textContent = word;
  el('bigWordOverlay').classList.add('visible');
  el('bigWordOverlay').setAttribute('aria-hidden', 'false');
}
function hideBigWord() {
  el('bigWordOverlay').classList.remove('visible');
  el('bigWordOverlay').setAttribute('aria-hidden', 'true');
}

// Navigation
function prevWeek() {
  if (currentWeek > 1) {
    currentWeek--;
    renderWeek();
  }
}
function nextWeek() {
  const maxWeek = effectiveMaxWeek();
  if (currentWeek < maxWeek) {
    currentWeek++;
    renderWeek();
  }
}

// Teacher panel: 3-finger tap on title
let touchTimer = null;
let touchStartTime = 0;
function initTeacherGesture() {
  const title = el('pageTitle');
  title.addEventListener('touchstart', (e) => {
    if (e.touches.length === 3) {
      touchStartTime = Date.now();
      touchTimer = setTimeout(() => {
        showPinDialog();
      }, 1500);
    }
  });
  title.addEventListener('touchend', () => {
    if (touchTimer) {
      clearTimeout(touchTimer);
      touchTimer = null;
    }
  });
  title.addEventListener('touchmove', () => {
    if (touchTimer) {
      clearTimeout(touchTimer);
      touchTimer = null;
    }
  });
  // Also support desktop: triple-click for testing
  title.addEventListener('click', (e) => {
    if (e.detail === 3) {
      showPinDialog();
    }
  });
}

function showPinDialog() {
  el('pinInput').value = '';
  el('pinError').textContent = '';
  el('pinDialog').classList.add('visible');
  el('pinInput').focus();
}
function hidePinDialog() {
  el('pinDialog').classList.remove('visible');
}
function checkPin() {
  const entered = el('pinInput').value;
  if (entered === DEFAULT_PIN) {
    hidePinDialog();
    showTeacherPanel();
  } else {
    el('pinError').textContent = 'Wrong PIN';
    el('pinInput').value = '';
    el('pinInput').focus();
  }
}

function showTeacherPanel() {
  el('levelSelect').value = settings.level;
  el('maxPagesRange').value = settings.max_week;
  el('maxPagesValue').textContent = settings.max_week;
  el('maxPagesField').classList.toggle('disabled', settings.level !== 'prek');
  el('teacherPanel').classList.add('visible');
}
function hideTeacherPanel() {
  el('teacherPanel').classList.remove('visible');
}
function saveTeacherSettings() {
  settings.level = el('levelSelect').value;
  settings.max_week = parseInt(el('maxPagesRange').value);
  saveSettings();
  hideTeacherPanel();
  // If current week is now locked, jump to max unlocked
  if (currentWeek > effectiveMaxWeek()) {
    currentWeek = effectiveMaxWeek();
  }
  renderWeek();
}

function initTeacherPanel() {
  el('pinSubmit').addEventListener('click', checkPin);
  el('pinCancel').addEventListener('click', hidePinDialog);
  el('pinInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') checkPin();
    if (e.key === 'Escape') hidePinDialog();
  });
  el('teacherSave').addEventListener('click', saveTeacherSettings);
  el('teacherClose').addEventListener('click', hideTeacherPanel);
  el('levelSelect').addEventListener('change', (e) => {
    el('maxPagesField').classList.toggle('disabled', e.target.value !== 'prek');
  });
  el('maxPagesRange').addEventListener('input', (e) => {
    el('maxPagesValue').textContent = e.target.value;
  });

  // Big word overlay: tap to close
  el('bigWordOverlay').addEventListener('click', hideBigWord);

  // Click outside to close teacher panel
  el('teacherPanel').addEventListener('click', (e) => {
    if (e.target === el('teacherPanel')) hideTeacherPanel();
  });
}

// Init
async function init() {
  loadSettings();
  applyURLParams();

  try {
    const r = await fetch('cvc-words.json?v=2');
    data = await r.json();
  } catch (e) {
    document.body.innerHTML = '<div class="container"><p>Failed to load CVC data. Make sure cvc-words.json is accessible.</p></div>';
    console.error(e);
    return;
  }

  initAudio();
  initTeacherGesture();
  initTeacherPanel();
  el('prevBtn').addEventListener('click', prevWeek);
  el('nextBtn').addEventListener('click', nextWeek);

  // Keyboard nav
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') prevWeek();
    if (e.key === 'ArrowRight') nextWeek();
    if (e.key === ' ') { e.preventDefault(); togglePlay(); }
  });

  renderWeek();
}

init();
