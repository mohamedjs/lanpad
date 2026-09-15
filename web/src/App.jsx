import React, { useEffect, useRef, useState } from 'react';
import { codeToKeysym } from './keymap.js';
import { push, move, flush, setStatusHandler, connect, token, setToken } from './sender.js';

const CMD_TARGETS = { Super_L: 'Super (⌘ = Ubuntu Super)', Control_L: 'Ctrl (⌘C = copy)', Alt_L: 'Alt' };

export default function App() {
  const [captured, setCaptured] = useState(false);
  const [status, setStatus] = useState('ready');
  const [cmdAs, setCmdAs] = useState(() => localStorage.getItem('cmdAs') || 'Super_L');
  const stage = useRef(null);
  const cmdRef = useRef(cmdAs);
  cmdRef.current = cmdAs;

  useEffect(() => { setStatusHandler(setStatus); connect(); }, []);
  useEffect(() => { const id = setInterval(flush, 10); return () => clearInterval(id); }, []);
  useEffect(() => { localStorage.setItem('cmdAs', cmdAs); }, [cmdAs]);

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
      if (!on) { release(); navigator.keyboard?.unlock?.(); }
    };

    const onMove = (e) => { if (locked()) move(e.movementX, e.movementY); };
    const onBtn = (down) => (e) => {
      if (!locked()) return;
      e.preventDefault();
      push('b', [1, 2, 3][e.button] || 1, down ? 1 : 0);
    };
    const onWheel = (e) => {
      if (!locked()) return;
      e.preventDefault();
      push('s', tick(e.deltaX), tick(e.deltaY));
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
      ['mousemove', onMove, document], ['mousedown', onBtn(true), document],
      ['mouseup', onBtn(false), document], ['wheel', onWheel, document, { passive: false }],
      ['keydown', onKey(true), window], ['keyup', onKey(false), window],
      ['contextmenu', (e) => e.preventDefault(), window],
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
        <span className={'status ' + (status === 'connected' ? 'ok' : '')}>{status}</span>
      </div>
    </div>
  );
}

const tick = (d) => (Math.round(d / 40) || (d ? Math.sign(d) : 0));
