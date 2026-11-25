const $ = (id) => document.getElementById(id);
let engines = [], current = null, busy = false, history = [];

function renderEngines() {
  $('engines').innerHTML = '';
  engines.forEach((e) => {
    const b = document.createElement('button');
    b.className = 'engine'; b.setAttribute('aria-pressed', String(e.id === current.id));
    b.innerHTML = '<span class="lamp"></span><span class="name"></span><span class="desc"></span><span class="kind"></span>';
    b.querySelector('.name').textContent = e.name;
    b.querySelector('.desc').textContent = e.tagline;
    b.querySelector('.kind').textContent = e.kind || '';
    b.onclick = () => selectEngine(e.id);
    $('engines').appendChild(b);
  });
}
function selectEngine(id) {
  current = engines.find((e) => e.id === id) || engines[0];
  $('voice').innerHTML = '';
  current.voices.forEach((v) => {
    const o = document.createElement('option');
    o.value = v.id; o.textContent = v.label; $('voice').appendChild(o);
  });
  $('note').textContent = current.note;
  $('speed').disabled = !current.speed;
  $('speed').style.opacity = current.speed ? '1' : '.4';
  renderEngines();
}
function setStatus(msg, isError) {
  $('status').textContent = isError ? 'Error: ' + msg : msg;
  $('status').classList.toggle('error', !!isError);
}
function updateCount() { $('count').textContent = $('script').value.length + ' chars'; }

let queue = [], cancelled = false;

function splitText(raw) {
  const text = raw.replace(/\r/g, '').trim();
  if (!text) return [];
  const parts = text.split(/(?<=[.!?。！？])\s+|\n{2,}/g).map(x => x.trim()).filter(Boolean);
  const MAX = 320;
  const pieces = [];
  for (let part of parts) {
    while (part.length > MAX) {
      let cut = -1;
      for (const sep of [', ', '; ', ': ', ' ']) {
        const i = part.lastIndexOf(sep, MAX);
        if (i > MAX / 2) { cut = i + sep.length; break; }
      }
      if (cut < 0) cut = MAX;
      pieces.push(part.slice(0, cut).trim());
      part = part.slice(cut).trim();
    }
    if (part) pieces.push(part);
  }
  const merged = [];
  for (const p of pieces) {
    if (merged.length && p.length < 16 && !/[.!?。！？]$/.test(p) && merged[merged.length - 1].length + p.length < MAX) {
      merged[merged.length - 1] += ' ' + p;
    } else {
      merged.push(p);
    }
  }
  return merged;
}

function concatWavs(buffers) {
  if (buffers.length === 1) return buffers[0].slice(0);
  const chunks = [];
  for (const b of buffers) {
    const dv = new DataView(b);
    const tag = (o, n) => String.fromCharCode.apply(null, new Uint8Array(b, o, n));
    if (tag(0, 4) !== 'RIFF' || tag(8, 4) !== 'WAVE') throw new Error('Unexpected audio format');
    let off = 12, fmt = null, pcm = null;
    while (off + 8 <= b.byteLength) {
      const id = tag(off, 4), size = dv.getUint32(off + 4, true);
      if (id === 'fmt ') fmt = new Uint8Array(b, off + 8, size);
      if (id === 'data') { pcm = new Uint8Array(b, off + 8, size); break; }
      off += 8 + size + (size % 2);
    }
    if (!fmt || !pcm) throw new Error('Unexpected WAV layout');
    chunks.push({fmt, pcm});
  }
  const f = chunks[0].fmt;
  const fdv = new DataView(f.buffer, f.byteOffset, f.byteLength);
  const channels = fdv.getUint16(2, true), rate = fdv.getUint32(4, true), bits = fdv.getUint16(14, true);
  const total = chunks.reduce((n, c) => n + c.pcm.length, 0);
  const out = new Uint8Array(44 + total);
  const odv = new DataView(out.buffer);
  const put = (o, str) => { for (let i = 0; i < str.length; i++) out[o + i] = str.charCodeAt(i); };
  put(0, 'RIFF'); odv.setUint32(4, 36 + total, true); put(8, 'WAVE'); put(12, 'fmt ');
  odv.setUint32(16, 16, true); odv.setUint16(20, 1, true); odv.setUint16(22, channels, true);
  odv.setUint32(24, rate, true); odv.setUint32(28, rate * channels * bits / 8, true);
  odv.setUint16(32, channels * bits / 8, true); odv.setUint16(34, bits, true);
  put(36, 'data'); odv.setUint32(40, total, true);
  let p = 44;
  for (const c of chunks) { out.set(c.pcm, p); p += c.pcm.length; }
  return out.buffer;
}

function playNext() {
  const player = $('player');
  if (!queue.length) { player.dataset.active = ''; return; }
  player.src = queue.shift();
  player.play().catch(() => {});
}
$('player').addEventListener('ended', playNext);

async function speak() {
  if (busy) return;
  const text = $('script').value.trim();
  if (!text) { setStatus('Type something in the script box first.', true); return; }
  const parts = splitText(text);
  busy = true;
  cancelled = false;
  queue = [];
  $('speak').disabled = true;
  $('stop').hidden = false;
  $('wave').classList.add('live');
  document.body.classList.add('generating');
  const player = $('player');
  player.pause();
  player.removeAttribute('src');
  player.classList.remove('ready');
  player.dataset.active = '';
  $('monitorHint').hidden = true;
  $('statTook').textContent = '--'; $('statLength').textContent = '--';
  $('statRate').textContent = '--'; $('statChars').textContent = text.length + ' chars';
  $('readout').classList.add('shown');
  const started = performance.now();
  let totalGen = 0, totalDur = 0;
  const buffers = [];
  try {
    for (let i = 0; i < parts.length; i++) {
      if (cancelled) break;
      setStatus('Generating part ' + (i + 1) + ' of ' + parts.length + '...');
      const res = await fetch('/api/speak', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({engine: current.id, text: parts[i], voice: $('voice').value, speed: parseFloat($('speed').value)})
      });
      const buf = await res.arrayBuffer();
      if (!res.ok) {
        let message = 'The engine returned an error.';
        try { const data = JSON.parse(new TextDecoder().decode(buf)); message = data.error || message; } catch (e) {}
        throw new Error(message);
      }
      if (cancelled) break;
      totalGen += parseFloat(res.headers.get('X-Gen-Seconds')) || 0;
      totalDur += parseFloat(res.headers.get('X-Audio-Seconds')) || 0;
      buffers.push(buf);
      queue.push(URL.createObjectURL(new Blob([buf], {type: 'audio/wav'})));
      player.classList.add('ready');
      if (!player.dataset.active) { player.dataset.active = '1'; playNext(); }
      $('statTook').textContent = totalGen.toFixed(2) + 's';
      $('statLength').textContent = totalDur.toFixed(2) + 's';
      $('statRate').textContent = totalGen > 0 ? (totalDur / totalGen).toFixed(1) + 'x realtime' : 'n/a';
    }
    setStatus(cancelled ? 'Stopped.' : 'Ready');
    if (buffers.length) {
      let fullUrl = URL.createObjectURL(new Blob([buffers[0]], {type: 'audio/wav'}));
      try { fullUrl = URL.createObjectURL(new Blob([concatWavs(buffers)], {type: 'audio/wav'})); } catch (e) {}
      $('download').href = fullUrl;
      const option = $('voice').selectedOptions[0];
      const voiceName = option ? option.textContent : 'default';
      const stamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
      $('takeInfo').textContent = current.name + ' / ' + voiceName + ', ' + stamp + ', ' + buffers.length + ' of ' + parts.length + ' parts';
      $('statChars').textContent = text.length + ' chars';
      history.unshift({url: fullUrl, who: current.name, text: text.slice(0, 70), secs: ((performance.now() - started) / 1000).toFixed(1)});
      history = history.slice(0, 8);
      renderHistory();
    }
  } catch (err) {
    setStatus(err.message || 'Something went wrong.', true);
  } finally {
    busy = false;
    $('speak').disabled = false;
    $('stop').hidden = true;
    $('wave').classList.remove('live');
    document.body.classList.remove('generating');
  }
}

function renderHistory() {
  $('recentWrap').hidden = history.length === 0;
  $('recent').innerHTML = '';
  history.forEach((h) => {
    const row = document.createElement('div'); row.className = 'clip';
    const who = document.createElement('span'); who.className = 'who'; who.textContent = h.who + ', ' + h.secs + 's';
    const what = document.createElement('span'); what.className = 'what'; what.textContent = h.text;
    const btn = document.createElement('button'); btn.textContent = 'Play';
    btn.onclick = () => { const p = $('player'); p.src = h.url; p.play().catch(() => {}); };
    row.append(who, what, btn); $('recent').appendChild(row);
  });
}
$('speak').onclick = speak;
$('stop').onclick = () => { cancelled = true; setStatus('Stopping after this part...'); };
$('script').addEventListener('input', updateCount);
$('script').addEventListener('keydown', (e) => { if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); speak(); } });
$('speed').oninput = () => { $('speedVal').textContent = parseFloat($('speed').value).toFixed(2); };
fetch('/api/engines').then((r) => r.json()).then((d) => {
  engines = d.engines;
  current = engines[0];
  selectEngine(current.id);
  setStatus('Ready');
}).catch((e) => setStatus('Could not reach the local server: ' + e.message, true));

fetch('/api/health').then((r) => r.json()).then((d) => {
  const models = d && d.models;
  if (models == null) return;
  $('modelsLabel').textContent = 'Models: ' + (Array.isArray(models) ? models.join(', ') : models);
}).catch(() => {});
