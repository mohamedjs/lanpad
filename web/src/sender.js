/* One WebSocket, events streamed out, nothing awaited. The old POST-per-batch
   version cost a round trip per frame, which is what made the pointer feel laggy. */
const queue = [];
let ws = null, ready = false, status = '', report = () => {}, rtt = 0;

const setStatus = (s) => { status = s; report(s); };
export const setStatusHandler = (fn) => { report = fn; fn(status); };

/* The token rides in the URL hash, but a hash is easy to lose — bookmarks, a typed
   URL, a copy-paste that drops it. Remember the last one that worked. */
const KEY = 'lanpadToken';
export const token = () => location.hash.slice(1) || localStorage.getItem(KEY) || '';
if (location.hash.slice(1)) localStorage.setItem(KEY, location.hash.slice(1));

export function setToken(t) {
  localStorage.setItem(KEY, t);
  location.hash = t;
  setStatus('reconnecting…');
  ws?.close();                                  // reconnect and re-authenticate
}

export function connect() {
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
  ws.onopen = () => ws.send(JSON.stringify({ t: token() }));    // first frame is the password
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.p !== undefined) {                    // probe came back: that is the true round trip
      rtt = Math.round(performance.now() - m.p);
      if (ready) setStatus(`connected · ${rtt} ms`);
      return;
    }
    ready = !!m.ok;
    setStatus(m.ok ? 'connected' : 'bad-token');
    if (m.ok) probe();
  };
  ws.onclose = () => {
    ready = false;
    if (status !== 'bad-token') setStatus('reconnecting…');
    setTimeout(connect, 700);                   // WiFi drops, laptop sleeps — just come back
  };
  ws.onerror = () => {};
}

const TYPE = { m: 1, b: 2, s: 3 };
const clamp = (v, n) => Math.max(-n, Math.min(n, Math.round(v)));

/* Pointer events go out as raw bytes — 5 per move instead of ~30 of JSON, and no
   stringify/parse on either end. Anything with a key name in it stays JSON. */
function encode(evs) {
  const v = new DataView(new ArrayBuffer(evs.length * 5));
  let o = 0;
  for (const e of evs) {
    v.setUint8(o, TYPE[e[0]]);
    if (e[0] === 'm') { v.setInt16(o + 1, clamp(e[1], 32767), true); v.setInt16(o + 3, clamp(e[2], 32767), true); o += 5; }
    else if (e[0] === 'b') { v.setUint8(o + 1, e[1]); v.setUint8(o + 2, e[2]); o += 3; }
    else { v.setInt8(o + 1, clamp(e[1], 127)); v.setInt8(o + 2, clamp(e[2], 127)); o += 3; }
  }
  return v.buffer.slice(0, o);
}

export function flush() {
  if (!ready || !queue.length) return;
  const ev = queue.splice(0, queue.length);
  ws.send(ev.every((e) => TYPE[e[0]]) ? encode(ev) : JSON.stringify({ ev }));
}

export const push = (...ev) => { queue.push(ev); flush(); };

export function move(dx, dy) {
  const last = queue[queue.length - 1];
  if (last && last[0] === 'm') { last[1] += dx; last[2] += dy; }   // coalesce within a tick
  else queue.push(['m', dx, dy]);
}

let probing = false;
function probe() {
  if (probing) return;
  probing = true;
  setInterval(() => {
    if (ready && ws.readyState === 1) ws.send(JSON.stringify({ p: performance.now() }));
  }, 1000);
}
export const lastRtt = () => rtt;
