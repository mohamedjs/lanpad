import React, { useEffect, useRef, useState } from 'react';
import { codeToKeysym } from './keymap.js';
import { push, move, flush, setStatusHandler, connect, setActive, token, setToken } from './sender.js';

const combo = (mods, key) => {
  mods.forEach((m) => push('k', m, 1));
  push('tap', key);
  [...mods].reverse().forEach((m) => push('k', m, 0));
};

// Chrome throttles mousemove to one event per repaint; pointerrawupdate is not throttled.
const RAW = 'onpointerrawupdate' in window ? 'pointerrawupdate' : 'mousemove';

const CMD_TARGETS = { Super_L: 'Super (⌘ = Ubuntu Super)', Control_L: 'Ctrl (⌘C = copy)', Alt_L: 'Alt' };

export default function App() {
  const [captured, setCaptured] = useState(false);
  const [status, setStatus] = useState('ready');
  const [cmdAs, setCmdAs] = useState(() => localStorage.getItem('cmdAs') || 'Super_L');
  const [invert, setInvert] = useState(() => localStorage.getItem('invert') === '1');
  const [swipe, setSwipe] = useState(() => localStorage.getItem('swipe') !== '0');
  const stage = useRef(null);
  const rate = useRef(0);
  const [hz, setHz] = useState(0);
  const cmdRef = useRef(cmdAs);
  cmdRef.current = cmdAs;
  const invertRef = useRef(invert);
  invertRef.current = invert;
  const swipeRef = useRef(swipe);
  swipeRef.current = swipe;

  useEffect(() => { setStatusHandler(setStatus); connect(); }, []);
  // 4ms is the browser's floor for a timer; moves coalesce between ticks, so this caps
  // the socket at ~250 frames/sec without adding meaningful delay
  useEffect(() => { const id = setInterval(flush, 4); return () => clearInterval(id); }, []);
  useEffect(() => {                                 // measured against the real elapsed
    let t0 = performance.now();                     // time, not an assumed 1000ms tick
    const id = setInterval(() => {
      const now = performance.now();
      setHz(Math.round((rate.current * 1000) / (now - t0)));
      rate.current = 0; t0 = now;
    }, 1000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => { localStorage.setItem('cmdAs', cmdAs); }, [cmdAs]);
  useEffect(() => { localStorage.setItem('invert', invert ? '1' : '0'); }, [invert]);
  useEffect(() => { localStorage.setItem('swipe', swipe ? '1' : '0'); }, [swipe]);

  function capture() {
    const el = stage.current;
    // fire-and-forget: an embedded/limited browser can leave these pending forever,
    // and the pointer lock is the part that actually matters
    el.requestFullscreen?.().catch(() => {});
    navigator.keyboard?.lock?.().catch(() => {});   // Chrome + https: lets Esc/Tab/⌘W through
    Promise.resolve(el.requestPointerLock({ unadjustedMovement: true }))  // raw deltas, no Mac accel
      .catch(() => Promise.resolve(el.requestPointerLock()))              // Safari / plain http
      .catch((err) => setStatus('cannot capture the mouse here: ' + err.message));
  }

  useEffect(() => {
    const locked = () => document.pointerLockElement === stage.current;

    const release = () => { push('rel'); flush(); };

    const onLockChange = () => {
      const on = locked();
      setCaptured(on);
      setActive(on);                              // keep the radio awake only while driving
      if (!on) { release(); navigator.keyboard?.unlock?.(); }
    };

    const onMove = (e) => {
      if (!locked()) return;
      rate.current++;
      // Only the event itself carries movementX/Y — the entries from
      // getCoalescedEvents() come back as zero on pointerrawupdate, which freezes
      // the pointer. Do not reach for them again.
      move(e.movementX, e.movementY);
    };
    const onBtn = (down) => (e) => {
      if (!locked()) return;
      e.preventDefault();
      push('b', [1, 2, 3][e.button] || 1, down ? 1 : 0);
    };
    // A Mac trackpad streams many tiny deltas (and momentum after you lift off), while
    // X11 scrolling is discrete button clicks. Accumulate, emit a click per STEP crossed.
    const acc = { x: 0, y: 0 };
    const sw = { x: 0, y: 0, t: 0, fired: false };
    const STEP = 28;
    const onWheel = (e) => {
      if (!locked()) return;
      e.preventDefault();
      const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1;   // lines / pages / px
      const sign = invertRef.current ? -1 : 1;
      acc.x += e.deltaX * unit * sign;
      acc.y += e.deltaY * unit * sign;
      // Flick detection. macOS keeps three- and four-finger swipes for itself, so these
      // are two-finger flicks: fast and long, which ordinary scrolling never is.
      // Left/right switch workspace, up opens the overview, down shows the desktop.
      if (swipeRef.current) {
        const now = performance.now();
        if (now - sw.t > 180) { sw.x = 0; sw.y = 0; sw.fired = false; }   // a new gesture
        sw.t = now;
        if (sw.fired) return;                       // swallow the tail of a fired flick
        sw.x += e.deltaX * unit; sw.y += e.deltaY * unit;
        const fast = Math.abs(e.deltaX) > 6 || Math.abs(e.deltaY) > 6;
        const horiz = Math.abs(sw.x) > Math.abs(sw.y) * 1.5 && Math.abs(sw.x) > 180;
        if (fast && horiz) {              // vertical is scrolling, never a gesture
          sw.fired = true;
          acc.x = acc.y = 0;
          combo(['Control_L', 'Alt_L'], sw.x > 0 ? 'Right' : 'Left');
          return;
        }
      }
      const tx = Math.trunc(acc.x / STEP), ty = Math.trunc(acc.y / STEP);
      if (!tx && !ty) return;
      acc.x -= tx * STEP; acc.y -= ty * STEP;
      if (e.ctrlKey) {                       // trackpad pinch arrives as ctrl+wheel
        push('k', 'Control_L', 1);
        push('s', tx, ty);
        push('k', 'Control_L', 0);
      } else {
        push('s', tx, ty);
      }
    };
    const onKey = (down) => (e) => {
      if (!locked()) return;
      e.preventDefault();                       // or ⌘W / ⌘R hits the Mac's browser instead
      if (e.repeat && down) return;             // X11 does its own key repeat
      let name = codeToKeysym(e.code);
      if (!name) return;
      if (name === 'Super_L' || name === 'Super_R') name = cmdRef.current;
      push('k', name, down ? 1 : 0);
    };

    const handlers = [
      ['pointerlockchange', onLockChange, document],
      [RAW, onMove, document], ['mousedown', onBtn(true), document],
      ['mouseup', onBtn(false), document], ['wheel', onWheel, document, { passive: false }],
      ['keydown', onKey(true), window], ['keyup', onKey(false), window],
      ['contextmenu', (e) => e.preventDefault(), window],
      // Chrome on macOS turns a two-finger horizontal swipe into back/forward navigation,
      // and a pinch into page zoom. Kill both here, captured or not — losing the page
      // mid-session is worse than any gesture it might otherwise pass through.
      ['wheel', (e) => e.preventDefault(), window, { passive: false }],
      ['gesturestart', (e) => e.preventDefault(), window, { passive: false }],
      ['gesturechange', (e) => e.preventDefault(), window, { passive: false }],
      ['gestureend', (e) => e.preventDefault(), window, { passive: false }],
      ['blur', () => { if (locked()) release(); }, window],
    ];
    for (const [ev, fn, target, opts] of handlers) target.addEventListener(ev, fn, opts);
    return () => { for (const [ev, fn, target] of handlers) target.removeEventListener(ev, fn); };
  }, []);

  return (
    <div className="app">
      <div ref={stage} className={'stage' + (captured ? ' live' : '')}
           onClick={status === 'bad-token' ? undefined : capture}>
        {status === 'bad-token' ? (
          <>
            <h1>Wrong password</h1>
            <p>The <code>#…</code> part of the address is missing. Paste the token the
              server printed, or reopen the full link.</p>
            <input
              className="token" placeholder="token" defaultValue={token()} autoFocus
              onClick={(e) => e.stopPropagation()}
              onChange={(e) => { setToken(e.target.value.trim().replace(/^#/, '')); setStatus('ready'); }}
            />
          </>
        ) : captured ? (
          <>
            <h1>Controlling Ubuntu</h1>
            <p>Your mouse and keyboard now drive the laptop. Press <kbd>Esc</kbd> to hand them back.</p>
          </>
        ) : (
          <>
            <h1>LANpad</h1>
            <p>Click to hand this Mac's mouse and keyboard to the Ubuntu laptop.</p>
            <p className="tip">Chrome, fullscreen, works best. macOS keeps ⌘Tab, ⌘Space and ⌘Q for itself.</p>
          </>
        )}
      </div>

      <div className="bar">
        <label>
          ⌘ sends
          <select value={cmdAs} onChange={(e) => setCmdAs(e.target.value)}>
            {Object.entries(CMD_TARGETS).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
          </select>
        </label>
        <label>
          <input type="checkbox" checked={invert} onChange={(e) => setInvert(e.target.checked)} />
          natural scrolling
        </label>
        <label>
          <input type="checkbox" checked={swipe} onChange={(e) => setSwipe(e.target.checked)} />
          swipe ←→ workspace
        </label>
        <span className={'status ' + (status.startsWith('connected') ? 'ok' : '')}>
          {status}{captured ? ` · ${hz} Hz` : ''}
        </span>
      </div>
    </div>
  );
}
