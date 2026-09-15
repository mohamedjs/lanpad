/* One WebSocket, events streamed out, nothing awaited. The old POST-per-batch
   version cost a round trip per frame, which is what made the pointer feel laggy. */
const queue = [];
let ws = null, ready = false, status = '', report = () => {};

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
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen = () => ws.send(JSON.stringify({ t: token() }));    // first frame is the password
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    ready = !!m.ok;
    setStatus(m.ok ? 'connected' : 'bad-token');
  };
  ws.onclose = () => {
    ready = false;
    if (status !== 'bad-token') setStatus('reconnecting…');
    setTimeout(connect, 700);                   // WiFi drops, laptop sleeps — just come back
  };
  ws.onerror = () => {};
}

export function flush() {
  if (!ready || !queue.length) return;
  ws.send(JSON.stringify({ ev: queue.splice(0, queue.length) }));
}

export const push = (...ev) => { queue.push(ev); flush(); };

export function move(dx, dy) {
  const last = queue[queue.length - 1];
  if (last && last[0] === 'm') { last[1] += dx; last[2] += dy; }   // coalesce within a tick
  else queue.push(['m', dx, dy]);
  flush();
}
