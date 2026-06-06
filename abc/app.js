/* ABC's Start — app.js
 * - Audio player with play/pause, scrubber, restart, loop toggle
 * - A-Z letter strip with tap-to-highlight on the chart
 *
 * Letter positions on the chart (4 rows x 7 cols) are stored as fractional
 * (x, y, w, h) coordinates so they scale with the image. The chart is laid
 * out left-to-right, top-to-bottom, with each cell occupying 1/7 of width
 * and ~1/4 of height, accounting for the "Yellow CD 1 Track 4" label area.
 */
(function () {
  'use strict';

  // --- Cell geometry for the chart ---
  // The original chart is 1600x1131. The "Yellow CD 1 Track 4" label
  // is erased in the top-left corner (x 4-32%, y 0-18.5%) — the rest of
  // the chart is intact, including the Egg and Gas pump tops which sit
  // at y ~13% (above the label baseline) and would be cut by a top crop.
  // Per-letter cell centers measured from the original chart by detecting
  // dark-pixel letter centroids in each row's letter band.
  var CENTERS = {
    // Row 0 (A-G)
    A: { cx: 0.135, cy: 0.295 }, B: { cx: 0.255, cy: 0.295 },
    C: { cx: 0.408, cy: 0.295 }, D: { cx: 0.500, cy: 0.295 },
    E: { cx: 0.624, cy: 0.295 }, F: { cx: 0.712, cy: 0.295 },
    G: { cx: 0.842, cy: 0.295 },
    // Row 1 (H-N)
    H: { cx: 0.130, cy: 0.495 }, I: { cx: 0.250, cy: 0.495 },
    J: { cx: 0.370, cy: 0.495 }, K: { cx: 0.490, cy: 0.495 },
    L: { cx: 0.620, cy: 0.495 }, M: { cx: 0.730, cy: 0.495 },
    N: { cx: 0.850, cy: 0.495 },
    // Row 2 (O-U)
    O: { cx: 0.133, cy: 0.695 }, P: { cx: 0.255, cy: 0.695 },
    Q: { cx: 0.378, cy: 0.695 }, R: { cx: 0.498, cy: 0.695 },
    S: { cx: 0.621, cy: 0.695 }, T: { cx: 0.743, cy: 0.695 },
    U: { cx: 0.866, cy: 0.695 },
    // Row 3 (V-Z)
    V: { cx: 0.133, cy: 0.880 }, W: { cx: 0.255, cy: 0.880 },
    X: { cx: 0.378, cy: 0.880 }, Y: { cx: 0.500, cy: 0.880 },
    Z: { cx: 0.620, cy: 0.880 }
  };
  var CELL_HW = 0.062;            // half-width: 12.4% total per cell
  var CELL_HH = 0.075;            // half-height: 15% total — covers picture body (rows are 13% tall, 7% gap)
  var CELL_HH_BOTTOM = 0.065;     // bottom row slightly shorter

  // --- Words for each letter (Chun-confirmed labels) ---
  var WORDS = {
    A: 'apple',     B: 'bell',      C: 'cat',       D: 'dog',
    E: 'egg',       F: 'fox',       G: 'gas pump',  H: 'hat',
    I: 'igloo',     J: 'jam',       K: 'kite',      L: 'log',
    M: 'mop',       N: 'net',       O: 'ox',        P: 'pig',
    Q: 'queen',     R: 'rabbit',    S: 'sun',       T: 'tent',
    U: 'umbrella',  V: 'van',       W: 'wagon',     X: 'axe',
    Y: 'yo-yo',     Z: 'zebra'
  };

  // --- Phonemes (American English). For stops/affricates/fricatives,
  // a "consonant + schwa" cue is the standard ESL technique and gives
  // TTS something pronounceable. For vowels, the sound word alone.
  // Vowels use the long/short sound in the picture word.
  var PHONEMES = {
    A: 'aah',  B: 'buh',  C: 'kuh',  D: 'duh',  E: 'eh',
    F: 'fuh',  G: 'guh',  H: 'huh',  I: 'ih',   J: 'juh',
    K: 'kuh',  L: 'luh',  M: 'muh',  N: 'nuh',  O: 'ah',
    P: 'puh',  Q: 'kwuh', R: 'ruh',  S: 'suh',  T: 'tuh',
    U: 'uh',   V: 'vuh',  W: 'wuh',  X: 'ks',   Y: 'yuh',
    Z: 'zuh'
  };

  // Cells in the bottom row use the slightly shorter height
  function cellRect(letter) {
    var c = CENTERS[letter];
    if (!c) return null;
    var hh = (/^[VWXYZ]$/.test(letter)) ? CELL_HH_BOTTOM : CELL_HH;
    return { x: c.cx - CELL_HW, y: c.cy - hh, w: CELL_HW * 2, h: hh * 2 };
  }

  // --- DOM ---
  var audio = document.getElementById('audio');
  var playBtn = document.getElementById('playBtn');
  var playIcon = document.getElementById('playIcon');
  var progressTrack = document.getElementById('progressTrack');
  var progressFill = document.getElementById('progressFill');
  var progressHandle = document.getElementById('progressHandle');
  var timeCurrent = document.getElementById('timeCurrent');
  var timeTotal = document.getElementById('timeTotal');
  var restartBtn = document.getElementById('restartBtn');
  var loopBtn = document.getElementById('loopBtn');
  var cellLayer = document.getElementById('cellLayer');
  var chartImg = document.getElementById('chartImg');

  // --- Build cell overlays (transparent buttons over each picture) ---
  for (var letter in CENTERS) {
    if (!Object.prototype.hasOwnProperty.call(CENTERS, letter)) continue;
    var r = cellRect(letter);
    if (!r) continue;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'cell';
    btn.dataset.letter = letter;
    btn.setAttribute('aria-label', letter + ': ' + PHONEMES[letter] + ', ' + WORDS[letter]);
    btn.style.left = (r.x * 100) + '%';
    btn.style.top = (r.y * 100) + '%';
    btn.style.width = (r.w * 100) + '%';
    btn.style.height = (r.h * 100) + '%';
    btn.addEventListener('click', (function (L, el) {
      return function () { onPictureTap(L, el); };
    })(letter, btn));
    cellLayer.appendChild(btn);
  }

  // --- Audio player ---
  function fmt(t) {
    if (!isFinite(t) || t < 0) t = 0;
    var m = Math.floor(t / 60);
    var s = Math.floor(t % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  function updateProgress() {
    if (!audio.duration) return;
    var pct = (audio.currentTime / audio.duration) * 100;
    progressFill.style.width = pct + '%';
    progressHandle.style.left = pct + '%';
    timeCurrent.textContent = fmt(audio.currentTime);
  }

  audio.addEventListener('loadedmetadata', function () {
    timeTotal.textContent = fmt(audio.duration);
  });
  audio.addEventListener('timeupdate', updateProgress);
  audio.addEventListener('ended', function () {
    if (!audio.loop) {
      setPlaying(false);
    }
  });

  function setPlaying(playing) {
    if (playing) {
      playIcon.textContent = '⏸';
      playBtn.classList.add('playing');
      playBtn.setAttribute('aria-label', 'Pause');
    } else {
      playIcon.textContent = '▶';
      playBtn.classList.remove('playing');
      playBtn.setAttribute('aria-label', 'Play');
    }
  }

  playBtn.addEventListener('click', function () {
    if (audio.paused) {
      audio.play().then(function () { setPlaying(true); }).catch(function (err) {
        console.error('Play failed:', err);
      });
    } else {
      audio.pause();
      setPlaying(false);
    }
  });

  restartBtn.addEventListener('click', function () {
    audio.currentTime = 0;
    if (audio.paused) {
      audio.play().then(function () { setPlaying(true); });
    }
  });

  loopBtn.addEventListener('click', function () {
    audio.loop = !audio.loop;
    loopBtn.classList.toggle('loop-on', audio.loop);
    loopBtn.setAttribute('aria-pressed', String(audio.loop));
  });

  // Scrubber
  function seekFromEvent(e) {
    if (!audio.duration) return;
    var rect = progressTrack.getBoundingClientRect();
    var x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    var pct = Math.max(0, Math.min(1, x / rect.width));
    audio.currentTime = pct * audio.duration;
    updateProgress();
  }
  var scrubbing = false;
  progressTrack.addEventListener('mousedown', function (e) {
    scrubbing = true;
    seekFromEvent(e);
  });
  progressTrack.addEventListener('touchstart', function (e) {
    scrubbing = true;
    seekFromEvent(e);
  }, { passive: true });
  document.addEventListener('mousemove', function (e) {
    if (scrubbing) seekFromEvent(e);
  });
  document.addEventListener('touchmove', function (e) {
    if (scrubbing) seekFromEvent(e);
  }, { passive: true });
  document.addEventListener('mouseup', function () { scrubbing = false; });
  document.addEventListener('touchend', function () { scrubbing = false; });
  progressTrack.addEventListener('keydown', function (e) {
    if (!audio.duration) return;
    if (e.key === 'ArrowLeft') {
      audio.currentTime = Math.max(0, audio.currentTime - 5);
      updateProgress();
    } else if (e.key === 'ArrowRight') {
      audio.currentTime = Math.min(audio.duration, audio.currentTime + 5);
      updateProgress();
    }
  });

  // --- Per-letter audio segments extracted from track2.mp3 ---
  // The first ~59 seconds of the audio is the alphabet song (one
  // continuous chant with no internal silences). Each letter gets a
  // ~2.25s slice from the start. Phonemes come from the song itself.
  var SOUNDS = {};
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach(function (L) {
    var a = new Audio('sounds/' + L + '.mp3');
    a.preload = 'auto';
    SOUNDS[L] = a;
  });

  // --- Voice selection (kept for fallback / future TTS use) ---
  var englishVoice = null;
  function pickEnglishVoice() {
    if (!('speechSynthesis' in window)) return;
    var voices = speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return;
    // Score each English voice. Higher = better.
    var best = null;
    var bestScore = -1;
    for (var i = 0; i < voices.length; i++) {
      var v = voices[i];
      if (!v.lang || v.lang.toLowerCase().indexOf('en') !== 0) continue;
      var name = (v.name || '').toLowerCase();
      var score = 0;
      // Premium / neural voice names (Microsoft, Apple, Google)
      if (/samantha|allison|tessa|karen|moira|ava|aria|jenny|guy|davis|jane|sonia|mia|andrew|emma|oliver|ava/.test(name)) score += 100;
      if (/neural|natural|online|enhanced|premium|wavenet|studio/.test(name)) score += 50;
      if (/google/.test(name)) score += 30;
      if (/microsoft/.test(name)) score += 20;
      // US English preferred
      if (v.lang === 'en-US' || v.lang === 'en_US') score += 25;
      // Cloud voices (not local) tend to be higher quality
      if (v.localService === false) score += 15;
      if (score > bestScore) { bestScore = score; best = v; }
    }
    englishVoice = best;
  }
  if ('speechSynthesis' in window) {
    pickEnglishVoice();
    if (typeof speechSynthesis.onvoiceschanged !== 'undefined') {
      speechSynthesis.onvoiceschanged = pickEnglishVoice;
    }
  }

  // --- Speak: play the extracted letter segment from the audio file ---
  function speak(letter) {
    var s = SOUNDS[letter];
    if (!s) return;
    // Don't interrupt the main "Track 2" song if it's playing.
    // Just play the small letter sound on top.
    try {
      s.currentTime = 0;
      var p = s.play();
      if (p && p.catch) p.catch(function (err) { console.error('Audio play failed:', err); });
    } catch (e) { console.error('speak error:', e); }
  }

  // --- Picture tap -> speak (no visual feedback) ---
  function onPictureTap(letter, cell) {
    speak(letter);
  }

  // initial state
  setPlaying(false);
})();
