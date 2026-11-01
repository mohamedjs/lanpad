/* Mobile WebSocket client for LANpad using low-latency binary framing. */

let ws = null;
let isReady = false;
let status = 'disconnected';
let onStatusChange = () => {};
let rtt = 0;
const queue = [];

const TYPE = { m: 1, b: 2, s: 3 };
const clamp = (v, n) => Math.max(-n, Math.min(n, Math.round(v)));

function encodeBinary(events) {
  // 5 bytes per move, 3 bytes per button/scroll
  const total = events.reduce((sum, e) => sum + (e[0] === 'm' ? 5 : 3), 0);
  const buf = new ArrayBuffer(total);
  const view = new DataView(buf);
  let offset = 0;

  for (const ev of events) {
    const kind = ev[0];
    view.setUint8(offset, TYPE[kind]);
    if (kind === 'm') {
      view.setInt16(offset + 1, clamp(ev[1], 32767), true);
      view.setInt16(offset + 3, clamp(ev[2], 32767), true);
      offset += 5;
    } else if (kind === 'b') {
      view.setUint8(offset + 1, ev[1]);
      view.setUint8(offset + 2, ev[2]);
      offset += 3;
    } else if (kind === 's') {
      view.setInt8(offset + 1, clamp(ev[1], 127));
      view.setInt8(offset + 2, clamp(ev[2], 127));
      offset += 3;
    }
  }
  return buf;
}

export function setStatusListener(cb) {
  onStatusChange = cb;
  cb(status, rtt);
}

export function connect(host, port, token) {
  if (ws) {
    try {
      ws.close();
    } catch (e) {}
  }

  status = 'connecting';
  onStatusChange(status, rtt);

  const url = `ws://${host}:${port}/ws`;
  try {
    ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      // Send token auth frame
      ws.send(JSON.stringify({ t: token }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.p !== undefined) {
          rtt = Math.round(Date.now() - msg.p);
          onStatusChange('connected', rtt);
          return;
        }
        if (msg.ok) {
          isReady = true;
          status = 'connected';
          onStatusChange(status, rtt);
          startProbe();
        } else if (msg.error) {
          status = 'bad-token';
          onStatusChange(status, rtt);
        }
      } catch (e) {}
    };

    ws.onerror = () => {
      status = 'error';
      onStatusChange(status, rtt);
    };

    ws.onclose = () => {
      isReady = false;
      if (status !== 'bad-token') {
        status = 'disconnected';
        onStatusChange(status, rtt);
      }
    };
  } catch (err) {
    status = 'error';
    onStatusChange(status, rtt);
  }
}

export function disconnect() {
  if (ws) {
    try {
      ws.close();
    } catch (e) {}
  }
  isReady = false;
  status = 'disconnected';
  onStatusChange(status, rtt);
}

let probeTimer = null;
function startProbe() {
  if (probeTimer) clearInterval(probeTimer);
  probeTimer = setInterval(() => {
    if (isReady && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ p: Date.now() }));
    }
  }, 1000);
}

export function sendEvents(...events) {
  if (!isReady || !ws || ws.readyState !== WebSocket.OPEN) return;
  const allBinary = events.every((e) => TYPE[e[0]]);
  if (allBinary) {
    ws.send(encodeBinary(events));
  } else {
    ws.send(JSON.stringify({ ev: events }));
  }
}
