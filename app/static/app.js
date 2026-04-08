/* === Auth guard === */
(function () {
  if (sessionStorage.getItem('fleet_auth') !== 'ok') {
    window.location.href = '/';
    return;
  }
  const user = sessionStorage.getItem('fleet_user') || 'martin';
  document.getElementById('user-name').textContent = user;
  document.getElementById('user-avatar').textContent = user.charAt(0).toUpperCase();
})();

/* === API helpers === */
const API = '/api/v1';

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

/* === Toast === */
function toast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => { el.className = 'toast'; }, 3500);
}

/* === Navigation === */
document.querySelectorAll('.header-nav button').forEach(btn => {
  btn.addEventListener('click', () => {
    const section = btn.dataset.section;
    // Toggle active nav
    document.querySelectorAll('.header-nav button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    // Toggle sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById('section-' + section).classList.add('active');
    // Load data on tab switch
    if (section === 'history') loadHistory();
    if (section === 'regions') loadRegions();
    if (section === 'config') loadConfig();
  });
});

/* === Logout === */
document.getElementById('btn-logout').addEventListener('click', () => {
  sessionStorage.clear();
  window.location.href = '/';
});

/* === Evaluate mode toggle === */
document.getElementById('eval-mode').addEventListener('change', function () {
  const isCity = this.value === 'city';
  document.getElementById('eval-city-group').style.display = isCity ? '' : 'none';
  document.getElementById('eval-lat-group').style.display = isCity ? 'none' : '';
  document.getElementById('eval-lon-group').style.display = isCity ? 'none' : '';
});

/* === Evaluate === */
document.getElementById('btn-evaluate').addEventListener('click', async () => {
  const mode = document.getElementById('eval-mode').value;
  let body;

  if (mode === 'city') {
    const city = document.getElementById('eval-city').value.trim();
    if (!city) { toast('Ingresa una ciudad', true); return; }
    body = { city };
  } else {
    const lat = parseFloat(document.getElementById('eval-lat').value);
    const lon = parseFloat(document.getElementById('eval-lon').value);
    if (isNaN(lat) || isNaN(lon)) { toast('Ingresa coordenadas validas', true); return; }
    body = { lat, lon };
  }

  const btn = document.getElementById('btn-evaluate');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    const data = await api('/fleet/evaluate', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    renderResult(data);
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Evaluar';
  }
});

function renderResult(d) {
  document.getElementById('eval-result').style.display = '';
  document.getElementById('res-region').textContent = d.region;
  document.getElementById('res-condition').textContent = d.condition;
  document.getElementById('res-condition').className = 'value condition-' + d.condition;
  document.getElementById('res-description').textContent = d.description;
  document.getElementById('res-temp').textContent = d.temperature_c + ' C';
  document.getElementById('res-wind').textContent = d.wind_speed_ms + ' m/s';
  document.getElementById('res-base').textContent = '$' + d.base_fare.toFixed(2);
  document.getElementById('res-pct').textContent = d.incentive_pct + '%';
  document.getElementById('res-amt').textContent = '$' + d.incentive_amt.toFixed(2);
  document.getElementById('res-total').textContent = '$' + d.total_investment.toFixed(2);

  const badge = document.getElementById('res-badge');
  badge.textContent = d.investment_level;
  badge.className = 'badge badge-' + d.investment_level;
}

/* === History === */
async function loadHistory() {
  const tbody = document.getElementById('history-body');
  const empty = document.getElementById('history-empty');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center"><span class="spinner"></span></td></tr>';

  try {
    const data = await api('/fleet/history?limit=50');
    if (data.length === 0) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = data.map(e => `
      <tr>
        <td><span class="badge badge-${e.investment_level}">${e.investment_level}</span></td>
        <td>$${parseFloat(e.base_fare).toFixed(2)}</td>
        <td>${e.incentive_pct}%</td>
        <td>$${parseFloat(e.incentive_amt).toFixed(2)}</td>
        <td><strong>$${parseFloat(e.total_investment).toFixed(2)}</strong></td>
        <td>${new Date(e.evaluated_at).toLocaleString()}</td>
      </tr>
    `).join('');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
  }
}

document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);

/* === Regions === */
async function loadRegions() {
  const tbody = document.getElementById('regions-body');
  const empty = document.getElementById('regions-empty');
  tbody.innerHTML = '<tr><td colspan="4" style="text-align:center"><span class="spinner"></span></td></tr>';

  try {
    const data = await api('/regions');
    if (data.length === 0) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = data.map(r => `
      <tr>
        <td><strong>${r.name}</strong></td>
        <td>${r.lat}</td>
        <td>${r.lon}</td>
        <td>${new Date(r.created_at).toLocaleDateString()}</td>
      </tr>
    `).join('');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
  }
}

document.getElementById('btn-add-region').addEventListener('click', async () => {
  const name = document.getElementById('region-name').value.trim();
  const lat = parseFloat(document.getElementById('region-lat').value);
  const lon = parseFloat(document.getElementById('region-lon').value);

  if (!name) { toast('Ingresa un nombre', true); return; }
  if (isNaN(lat) || isNaN(lon)) { toast('Ingresa coordenadas validas', true); return; }

  try {
    await api('/regions', {
      method: 'POST',
      body: JSON.stringify({ name, lat, lon }),
    });
    toast('Region creada');
    document.getElementById('region-name').value = '';
    document.getElementById('region-lat').value = '';
    document.getElementById('region-lon').value = '';
    loadRegions();
  } catch (e) {
    toast(e.message, true);
  }
});

/* === Config === */
async function loadConfig() {
  const tbody = document.getElementById('config-body');
  const empty = document.getElementById('config-empty');
  tbody.innerHTML = '<tr><td colspan="4" style="text-align:center"><span class="spinner"></span></td></tr>';

  try {
    const data = await api('/config/incentive');
    if (data.length === 0) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = data.map(c => `
      <tr>
        <td><span class="condition-${c.condition}"><strong>${c.condition}</strong></span></td>
        <td>
          <input type="number" step="0.01" value="${c.base_fare}"
                 id="cfg-fare-${c.condition}" style="width:100px;padding:6px 10px;border:2px solid var(--rappi-gray-200);border-radius:6px">
        </td>
        <td>
          <input type="number" step="0.1" min="0" max="100" value="${c.incentive_pct}"
                 id="cfg-pct-${c.condition}" style="width:80px;padding:6px 10px;border:2px solid var(--rappi-gray-200);border-radius:6px">
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="saveConfig('${c.condition}')">Guardar</button>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
  }
}

async function saveConfig(condition) {
  const baseFare = parseFloat(document.getElementById('cfg-fare-' + condition).value);
  const pct = parseFloat(document.getElementById('cfg-pct-' + condition).value);

  if (isNaN(baseFare) || baseFare <= 0) { toast('Tarifa invalida', true); return; }
  if (isNaN(pct) || pct < 0 || pct > 100) { toast('Porcentaje debe ser entre 0 y 100', true); return; }

  try {
    await api('/config/incentive/' + condition, {
      method: 'PUT',
      body: JSON.stringify({ base_fare: baseFare, incentive_pct: pct }),
    });
    toast('Configuracion actualizada');
  } catch (e) {
    toast(e.message, true);
  }
}

// Expose to onclick
window.saveConfig = saveConfig;
