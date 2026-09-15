function toJson(obj) {
  try { return JSON.stringify(obj, null, 2); } catch(e) { return String(obj); }
}

// WebSocket client and chart state
let socket = null;
let forecastChart = null;
let chartData = { labels: [], datasets: [{ label: 'Predicted Load', data: [], borderColor: 'rgba(13,110,253,1)', backgroundColor: 'rgba(13,110,253,0.1)', fill: true }] };

function initChart() {
  const ctx = document.getElementById('forecastChart').getContext('2d');
  forecastChart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
      animation: false,
      responsive: true,
      scales: { x: { display: true }, y: { display: true, beginAtZero: false } }
    }
  });
}

async function fetchForecast() {
  const hours = parseInt(document.getElementById('hours').value || '12', 10);
  const res = await fetch('/forecast', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hours }) });
  return res.json();
}

async function fetchAnomalies() {
  const res = await fetch('/anomalies');
  return res.json();
}

async function fetchRecommend(forecast, anomalies) {
  const res = await fetch('/recommend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ forecast, anomalies }) });
  return res.json();
}

document.getElementById('btnForecast').addEventListener('click', async () => {
  document.getElementById('forecastSummary').textContent = 'Running...';
  try {
    const data = await fetchForecast();
    const f = data.forecast || data;
    document.getElementById('forecastArea') && (document.getElementById('forecastArea').textContent = '');
    // update chart
    const labels = Object.keys(f);
    const values = Object.values(f).map(v => Number(v));
    chartData.labels = labels;
    chartData.datasets[0].data = values;
    if (!forecastChart) initChart(); else forecastChart.update();
    // show summary
    const peak = Math.max(...values);
    const avg = (values.reduce((a,b)=>a+b,0)/values.length).toFixed(1);
    document.getElementById('forecastSummary').innerHTML = `<strong>Peak:</strong> ${peak.toFixed(1)} &nbsp; <strong>Avg:</strong> ${avg}`;
    // notify via websocket
    if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'client_forecast_request' }));
  } catch (e) {
    document.getElementById('forecastSummary').textContent = 'Error: ' + e;
  }
});

document.getElementById('btnAnomalies').addEventListener('click', async () => {
  document.getElementById('anomalyList').innerHTML = '<li class="list-group-item">Running...</li>';
  try {
    const data = await fetchAnomalies();
    const list = document.getElementById('anomalyList'); list.innerHTML = '';
    if (data.timestamps && data.timestamps.length) {
      data.timestamps.forEach(ts => { const li = document.createElement('li'); li.className='list-group-item'; li.textContent = ts; list.appendChild(li); });
    } else {
      list.innerHTML = '<li class="list-group-item">(no anomalies)</li>';
    }
    if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'client_anomalies_request' }));
  } catch (e) {
    document.getElementById('anomalyList').innerHTML = '<li class="list-group-item">Error</li>';
  }
});

document.getElementById('btnRecommend').addEventListener('click', async () => {
  document.getElementById('recommendArea').textContent = 'Running...';
  try {
    const f = await fetchForecast();
    const a = await fetchAnomalies();
    const r = await fetchRecommend(f.forecast, a);
    // format recommendations as cards
    const area = document.getElementById('recommendArea');
    area.innerHTML = '';
    if (r.actions && r.actions.actions) {
      r.actions.actions.forEach(act => {
        const card = document.createElement('div'); card.className='card mb-2';
        const body = document.createElement('div'); body.className='card-body p-2';
        body.innerHTML = `<strong>${act.type}</strong><div class="small text-muted">${act.description}</div>`;
        card.appendChild(body); area.appendChild(card);
      });
    }
    const pre = document.createElement('pre'); pre.className='mt-2 small'; pre.textContent = (r.brief && r.brief.brief) ? r.brief.brief : toJson(r.brief || r);
    area.appendChild(pre);
    if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'client_recommend_request' }));
  } catch (e) {
    document.getElementById('recommendArea').textContent = 'Error: ' + e;
  }
});

// WebSocket connect
document.getElementById('btnConnect').addEventListener('click', () => {
  const key = document.getElementById('apiKeyInput').value || '';
  if (socket) socket.close();
  const proto = (location.protocol === 'https:') ? 'wss' : 'ws';
  socket = new WebSocket(`${proto}://${location.host}/ws?token=${encodeURIComponent(key)}`);
  socket.onopen = () => { document.getElementById('wsStatus').textContent = 'Connected'; };
  socket.onclose = () => { document.getElementById('wsStatus').textContent = 'Disconnected'; };
  socket.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'forecast') {
        const f = msg.payload.forecast;
        chartData.labels = Object.keys(f);
        chartData.datasets[0].data = Object.values(f).map(v => Number(v));
        if (!forecastChart) initChart(); else forecastChart.update();
      } else if (msg.type === 'anomalies') {
        const list = document.getElementById('anomalyList'); list.innerHTML = '';
        (msg.payload.timestamps||[]).forEach(ts => { const li = document.createElement('li'); li.textContent = ts; list.appendChild(li); });
      } else if (msg.type === 'recommend') {
        const area = document.getElementById('recommendArea');
        area.innerHTML = '<strong>Realtime recommendation</strong><br/>' + (msg.payload.brief && msg.payload.brief.brief ? msg.payload.brief.brief : JSON.stringify(msg.payload));
      }
    } catch(e) { console.error(e); }
  };
});

// initialize chart on load
window.addEventListener('load', () => { initChart(); });
