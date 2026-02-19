'use strict';

/* ══════════════════════════════════════════════════
   CONFIG — all tuneable values in one place.
   Change a number, save, refresh — no hunting through code.
══════════════════════════════════════════════════ */
const CFG = {
  /* ── Timing (milliseconds) ── */
  INITIAL_DELAY   : 1100,   // delay before chatbox first appears on load
  HIDE_DUR        : 370,    // how fast chatbox shrinks into the trunk
  APPEAR_DUR      : 2900,   // leaf-to-center flight time (~3 s as requested)
  APPEAR_EASE     : 'cubic-bezier(0.34,1.15,0.64,1)',  // springy ease-out

  /* ── Leaf particle system ── */
  LEAF_COUNT      : 42,     // total leaves on screen
  LEAF_SPEED_MIN  : 0.055,  // px per animation frame (very slow)
  LEAF_SPEED_MAX  : 0.30,
  LEAF_SIZE_MIN   : 5,      // px radius
  LEAF_SIZE_MAX   : 16,
  LEAF_OPA_MIN    : 0.22,   // distant leaves are more transparent
  LEAF_OPA_MAX    : 0.72,
  LEAF_SWAY_AMP   : 0.28,   // max horizontal wobble amplitude
  LEAF_SWAY_SPD   : 0.006,  // wobble cycle speed (radians/frame)
};

/* ══════════════════════════════════════════════════
   DOM REFERENCES
══════════════════════════════════════════════════ */
const leafCanvas = document.getElementById('leaf-canvas');
const lctx       = leafCanvas.getContext('2d');
const cbWrap     = document.getElementById('cb-wrap');
const msgBox     = document.getElementById('messages');
const cbInput    = document.getElementById('cb-input');
const sendBtn    = document.getElementById('cb-send');
const envLabel   = document.getElementById('env-label');

/* ══════════════════════════════════════════════════
   CHATBOX STATE MACHINE
   HIDDEN → APPEARING → VISIBLE → HIDING → HIDDEN → …
══════════════════════════════════════════════════ */
const S = Object.freeze({ HIDDEN: 0, APPEARING: 1, VISIBLE: 2, HIDING: 3 });
let chatState = S.HIDDEN;

/* ══════════════════════════════════════════════════
   ❶  LEAF PARTICLE SYSTEM
══════════════════════════════════════════════════ */
let leaves     = [];
let pausedLeaf = null;   // the leaf chosen as chatbox birth-point

function resizeCanvas() {
  leafCanvas.width  = window.innerWidth;
  leafCanvas.height = window.innerHeight;
}

class Leaf {
  constructor(scatter = false) { this.reset(scatter); }

  reset(scatter = false) {
    this.x       = Math.random() * leafCanvas.width;
    this.y       = scatter
                   ? Math.random() * leafCanvas.height          // spread on init
                   : -(Math.random() * leafCanvas.height * 0.6); // above viewport
    this.size    = CFG.LEAF_SIZE_MIN + Math.random() * (CFG.LEAF_SIZE_MAX - CFG.LEAF_SIZE_MIN);
    this.speed   = CFG.LEAF_SPEED_MIN + Math.random() * (CFG.LEAF_SPEED_MAX - CFG.LEAF_SPEED_MIN);
    this.sway    = CFG.LEAF_SWAY_AMP * (0.4 + Math.random() * 0.8);
    this.wobble  = Math.random() * Math.PI * 2;
    this.wobSpd  = CFG.LEAF_SWAY_SPD * (0.6 + Math.random() * 0.8);
    this.rot     = Math.random() * Math.PI * 2;
    this.rotSpd  = (Math.random() - 0.5) * 0.009;
    this.opacity = CFG.LEAF_OPA_MIN + Math.random() * (CFG.LEAF_OPA_MAX - CFG.LEAF_OPA_MIN);
    /* Colour: yellow-green to deep green range */
    this.hue     = 82  + Math.random() * 52;
    this.sat     = 50  + Math.random() * 38;
    this.lit     = 24  + Math.random() * 24;
    this.paused  = false;
  }

  update() {
    if (this.paused) return;
    this.wobble += this.wobSpd;
    this.x      += Math.sin(this.wobble) * this.sway;
    this.y      += this.speed;
    this.rot    += this.rotSpd;
    if (this.y > leafCanvas.height + 30) this.reset(false);
  }

  draw(ctx) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rot);
    ctx.globalAlpha = this.opacity;
    ctx.fillStyle   = `hsl(${this.hue},${this.sat}%,${this.lit}%)`;

    /* Almond leaf shape */
    const h = this.size, w = this.size * 0.52;
    ctx.beginPath();
    ctx.moveTo(0, -h);
    ctx.bezierCurveTo( w * 1.1, -h * 0.25,  w, h * 0.42, 0, h);
    ctx.bezierCurveTo(-w,        h * 0.42, -w * 1.1, -h * 0.25, 0, -h);
    ctx.closePath();
    ctx.fill();

    /* Central vein */
    ctx.strokeStyle = `hsl(${this.hue},38%,${this.lit + 12}%)`;
    ctx.globalAlpha = this.opacity * 0.38;
    ctx.lineWidth   = 0.55;
    ctx.beginPath();
    ctx.moveTo(0, -h * 0.78);
    ctx.lineTo(0,  h * 0.78);
    ctx.stroke();
    ctx.restore();
  }
}

function initLeaves() {
  leaves = Array.from({ length: CFG.LEAF_COUNT }, () => new Leaf(true));
}

/** Returns screen coords of a randomly chosen visible leaf, and pauses it. */
function pickLeaf() {
  const pool = leaves.filter(l =>
    !l.paused &&
    l.y > leafCanvas.height * 0.08 &&
    l.y < leafCanvas.height * 0.78 &&
    l.x > leafCanvas.width  * 0.06 &&
    l.x < leafCanvas.width  * 0.94
  );
  if (!pool.length) return { x: leafCanvas.width / 2, y: leafCanvas.height * 0.28 };
  pausedLeaf = pool[Math.floor(Math.random() * pool.length)];
  pausedLeaf.paused = true;
  return { x: pausedLeaf.x, y: pausedLeaf.y };
}

function releaseLeaf() {
  if (pausedLeaf) { pausedLeaf.paused = false; pausedLeaf = null; }
}

function tickLeaves() {
  lctx.clearRect(0, 0, leafCanvas.width, leafCanvas.height);
  leaves.forEach(l => { l.update(); l.draw(lctx); });
  requestAnimationFrame(tickLeaves);
}

/* ══════════════════════════════════════════════════
   ❷  CHATBOX ANIMATIONS
══════════════════════════════════════════════════ */

/**
 * First appearance on page load — grows from trunk centre.
 * Faster than the leaf version since there's no travel distance.
 */
function appearFromTrunk() {
  if (chatState === S.VISIBLE || chatState === S.APPEARING) return;
  chatState = S.APPEARING;
  envLabel.classList.add('invisible');

  cbWrap.style.transition = 'none';
  cbWrap.style.transform  = 'translate(-50%, -50%) scale(0.02)';
  void cbWrap.offsetWidth; // force reflow — required for transition to fire

  const dur = Math.round(CFG.APPEAR_DUR * 0.55);
  cbWrap.style.transition = `transform ${dur}ms ${CFG.APPEAR_EASE}`;
  cbWrap.style.transform  = 'translate(-50%, -50%) scale(1)';

  setTimeout(() => {
    chatState = S.VISIBLE;
    cbInput.focus();
    scrollBottom();
  }, dur);
}

/**
 * Response received — pick a random visible leaf, pause it,
 * then grow the chatbox from that leaf's position to the screen centre.
 */
function appearFromLeaf() {
  if (chatState === S.VISIBLE || chatState === S.APPEARING) return;
  chatState = S.APPEARING;
  envLabel.classList.add('invisible');

  const leaf = pickLeaf();
  const cx   = window.innerWidth  / 2;
  const cy   = window.innerHeight / 2;
  /* Offset of leaf from screen centre — chatbox will start there */
  const dx   = leaf.x - cx;
  const dy   = leaf.y - cy;

  /* Start: chatbox lives at leaf position, nearly invisible */
  cbWrap.style.transition = 'none';
  cbWrap.style.transform  =
    `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(0.04)`;
  void cbWrap.offsetWidth;

  /* Animate: simultaneously move to centre AND expand */
  cbWrap.style.transition = `transform ${CFG.APPEAR_DUR}ms ${CFG.APPEAR_EASE}`;
  cbWrap.style.transform  = 'translate(-50%, -50%) scale(1)';

  setTimeout(() => {
    releaseLeaf();     // leaf continues falling
    chatState = S.VISIBLE;
    cbInput.focus();
    scrollBottom();
  }, CFG.APPEAR_DUR);
}

/**
 * User submits a message — chatbox shrinks into the trunk.
 * @param {Function} onDone  called when animation completes
 */
function hideChatbox(onDone) {
  if (chatState !== S.VISIBLE) { if (onDone) onDone(); return; }
  chatState = S.HIDING;

  /* Drift slightly downward (toward trunk) while shrinking */
  const drift = Math.min(window.innerHeight * 0.12, 80);
  cbWrap.style.transition = `transform ${CFG.HIDE_DUR}ms ease-in`;
  cbWrap.style.transform  =
    `translate(-50%, calc(-50% + ${drift}px)) scale(0.02)`;

  setTimeout(() => {
    chatState = S.HIDDEN;
    envLabel.classList.remove('invisible');
    if (onDone) onDone();
  }, CFG.HIDE_DUR);
}

/* ══════════════════════════════════════════════════
   ❸  MESSAGE UTILITIES
══════════════════════════════════════════════════ */
function scrollBottom() {
  msgBox.scrollTop = msgBox.scrollHeight;
}

function addMessage(text, isUser) {
  const d   = document.createElement('div');
  d.className = 'msg ' + (isUser ? 'user' : 'bot');

  const lbl = document.createElement('div');
  lbl.className   = 'lbl';
  lbl.textContent = isUser ? 'You' : 'Clinical AI';
  d.appendChild(lbl);

  /* Preserve line-breaks in bot responses */
  if (isUser) {
    d.appendChild(document.createTextNode(text));
  } else {
    const p = document.createElement('span');
    p.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    d.appendChild(p);
  }

  msgBox.appendChild(d);
  scrollBottom();
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/* ══════════════════════════════════════════════════
   ❹  SEND / FLASK API
══════════════════════════════════════════════════ */
async function handleSend() {
  const msg = cbInput.value.trim();
  if (!msg || chatState !== S.VISIBLE) return;

  cbInput.value    = '';
  sendBtn.disabled = true;
  addMessage(msg, true);

  hideChatbox(async () => {
    envLabel.textContent = 'Consulting the medical knowledge base…';

    try {
      /* ── Real Flask call ──
         Sends 'msg' to /get, returns plain-text response.
         Matches your existing app.py backend exactly.          */
      const fd  = new FormData();
      fd.append('msg', msg);

      const res   = await fetch('/get', { method: 'POST', body: fd });
      const reply = await res.text();

      addMessage(reply, false);

    } catch (err) {
      addMessage('Connection error — please check your network and try again.', false);
      console.error('Fetch error:', err);
    } finally {
      sendBtn.disabled = false;
      envLabel.textContent = 'A tranquil space for medical guidance…';
      appearFromLeaf();
    }
  });
}

/* ══════════════════════════════════════════════════
   ❺  EVENT LISTENERS
══════════════════════════════════════════════════ */
sendBtn.addEventListener('click', handleSend);

cbInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

window.addEventListener('resize', () => {
  resizeCanvas();
  if (chatState === S.VISIBLE) {
    /* Keep chatbox centred after resize */
    cbWrap.style.transition = 'none';
    cbWrap.style.transform  = 'translate(-50%, -50%) scale(1)';
  }
});

/* ══════════════════════════════════════════════════
   ❻  BOOT
══════════════════════════════════════════════════ */
resizeCanvas();
initLeaves();
tickLeaves();
setTimeout(appearFromTrunk, CFG.INITIAL_DELAY);