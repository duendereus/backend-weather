/* ==========================================================================
   Fleet Investment Dashboard — app.js
   ========================================================================== */

/* === Auth guard === */
(function () {
  if (sessionStorage.getItem('fleet_auth') !== 'ok') {
    window.location.href = '/';
    return;
  }
  var user = sessionStorage.getItem('fleet_user') || 'martin';
  document.getElementById('user-name').textContent = user;
  document.getElementById('user-avatar').textContent = user.charAt(0).toUpperCase();
})();

/* === API helpers === */
var API = '/api/v1';

function extractErrorMessage(err) {
  if (!err) return 'Error desconocido';
  if (typeof err === 'string') return err;
  if (err.detail) {
    if (typeof err.detail === 'string') return err.detail;
    // Pydantic validation errors come as array
    if (Array.isArray(err.detail)) {
      return err.detail.map(function (e) {
        var field = (e.loc || []).slice(1).join(' > ') || 'campo';
        return field + ': ' + (e.msg || 'invalido');
      }).join('. ');
    }
    return String(err.detail);
  }
  if (err.message) return err.message;
  return 'Error desconocido';
}

async function api(path, opts) {
  opts = opts || {};
  var res;
  try {
    res = await fetch(API + path, {
      headers: { 'Content-Type': 'application/json' },
      method: opts.method || 'GET',
      body: opts.body || undefined,
    });
  } catch (networkErr) {
    throw new Error('No se pudo conectar con el servidor. Verifica que el servicio este corriendo.');
  }

  // 204 No Content (e.g. DELETE)
  if (res.status === 204) return null;

  var data;
  try {
    data = await res.json();
  } catch (e) {
    if (!res.ok) throw new Error('Error del servidor (' + res.status + ' ' + res.statusText + ')');
    return null;
  }

  if (!res.ok) {
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

/* === Toast === */
var toastTimer = null;
function toast(msg, isError) {
  var el = document.getElementById('toast');
  el.textContent = String(msg);
  el.className = 'toast show' + (isError ? ' error' : '');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { el.className = 'toast'; }, 4000);
}

/* === Validation helpers === */
function clearFieldError(inputId) {
  var input = document.getElementById(inputId);
  if (input) input.classList.remove('invalid');
  var err = document.getElementById(inputId + '-error');
  if (err) err.textContent = '';
}

function setFieldError(inputId, msg) {
  var input = document.getElementById(inputId);
  if (input) input.classList.add('invalid');
  var err = document.getElementById(inputId + '-error');
  if (err) err.textContent = msg;
}

function validateLat(value) {
  if (value === '' || isNaN(Number(value))) return 'Ingresa un numero valido';
  var n = Number(value);
  if (n < -90 || n > 90) return 'Debe estar entre -90 y 90';
  return null;
}

function validateLon(value) {
  if (value === '' || isNaN(Number(value))) return 'Ingresa un numero valido';
  var n = Number(value);
  if (n < -180 || n > 180) return 'Debe estar entre -180 y 180';
  return null;
}

/* === Navigation === */
document.querySelectorAll('.header-nav button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var section = btn.dataset.section;
    document.querySelectorAll('.header-nav button').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    document.querySelectorAll('.section').forEach(function (s) { s.classList.remove('active'); });
    document.getElementById('section-' + section).classList.add('active');
    if (section === 'history') loadHistory();
    if (section === 'scheduled') loadScheduled();
    if (section === 'regions') loadRegions();
    if (section === 'config') loadConfig();
    if (section === 'evaluate') loadRegionDropdown();
  });
});

/* === Logout === */
document.getElementById('btn-logout').addEventListener('click', function () {
  sessionStorage.clear();
  window.location.href = '/';
});

/* =========================================================================
   EVALUATE
   ========================================================================= */

var evalMode = document.getElementById('eval-mode');

var evalHint = document.getElementById('eval-hint');
var HINT_REGION = 'Administra las regiones disponibles desde <a href="#" id="link-to-regions" style="color:var(--rappi-orange);font-weight:600">Regiones</a>';
var HINT_CITY = 'La ciudad se registrara como region automaticamente si la consulta al clima es exitosa.';
var HINT_COORDS = 'Latitud: -90 a 90. Longitud: -180 a 180.';

function updateEvalFields() {
  var mode = evalMode.value;
  document.getElementById('eval-region-group').style.display = mode === 'region' ? '' : 'none';
  document.getElementById('eval-city-group').style.display = mode === 'city' ? '' : 'none';
  document.getElementById('eval-lat-group').style.display = mode === 'coords' ? '' : 'none';
  document.getElementById('eval-lon-group').style.display = mode === 'coords' ? '' : 'none';
  // Update hint
  if (mode === 'region') evalHint.innerHTML = HINT_REGION;
  else if (mode === 'city') evalHint.innerHTML = HINT_CITY;
  else evalHint.innerHTML = HINT_COORDS;
  // Re-attach link handler
  bindRegionLink();
  // Clear validation
  ['eval-lat', 'eval-lon'].forEach(clearFieldError);
}

evalMode.addEventListener('change', updateEvalFields);

// Navigate to regions tab from hint link
function bindRegionLink() {
  var link = document.getElementById('link-to-regions');
  if (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector('.header-nav button[data-section="regions"]').click();
    });
  }
}
bindRegionLink();

// Load regions into dropdown
async function loadRegionDropdown() {
  var select = document.getElementById('eval-region');
  try {
    var regions = await api('/regions');
    // Keep first placeholder option
    select.innerHTML = '<option value="">-- Selecciona una region --</option>';
    regions.forEach(function (r) {
      var opt = document.createElement('option');
      opt.value = r.name;
      opt.textContent = r.name + ' (' + r.lat + ', ' + r.lon + ')';
      select.appendChild(opt);
    });
  } catch (e) {
    // Silently fail — dropdown just stays empty
  }
}

// Validate on keyup for coord fields
document.getElementById('eval-lat').addEventListener('input', function () {
  clearFieldError('eval-lat');
  var err = validateLat(this.value);
  if (err && this.value !== '') setFieldError('eval-lat', err);
});

document.getElementById('eval-lon').addEventListener('input', function () {
  clearFieldError('eval-lon');
  var err = validateLon(this.value);
  if (err && this.value !== '') setFieldError('eval-lon', err);
});

document.getElementById('btn-evaluate').addEventListener('click', async function () {
  var mode = evalMode.value;
  var body;

  if (mode === 'region') {
    var regionName = document.getElementById('eval-region').value;
    if (!regionName) {
      toast('Selecciona una region del listado', true);
      return;
    }
    body = { city: regionName };

  } else if (mode === 'city') {
    var city = document.getElementById('eval-city').value.trim();
    if (!city) {
      toast('Ingresa el nombre de una ciudad', true);
      return;
    }
    if (city.length < 2) {
      toast('El nombre de la ciudad debe tener al menos 2 caracteres', true);
      return;
    }
    body = { city: city };

  } else {
    // coords
    var latVal = document.getElementById('eval-lat').value;
    var lonVal = document.getElementById('eval-lon').value;
    var latErr = validateLat(latVal);
    var lonErr = validateLon(lonVal);

    clearFieldError('eval-lat');
    clearFieldError('eval-lon');

    if (latErr) setFieldError('eval-lat', latErr);
    if (lonErr) setFieldError('eval-lon', lonErr);
    if (latErr || lonErr) {
      toast('Corrige los errores en las coordenadas', true);
      return;
    }
    body = { lat: Number(latVal), lon: Number(lonVal) };
  }

  var btn = document.getElementById('btn-evaluate');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    var data = await api('/fleet/evaluate', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    renderResult(data);
    toast('Evaluacion completada para ' + data.region);
  } catch (e) {
    toast(e.message, true);
    document.getElementById('eval-result').style.display = 'none';
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
  document.getElementById('res-temp').textContent = d.temperature_c.toFixed(1) + ' C';
  document.getElementById('res-wind').textContent = d.wind_speed_ms.toFixed(1) + ' m/s';
  document.getElementById('res-base').textContent = '$' + d.base_fare.toFixed(2);
  document.getElementById('res-pct').textContent = d.incentive_pct + '%';
  document.getElementById('res-amt').textContent = '$' + d.incentive_amt.toFixed(2);
  document.getElementById('res-total').textContent = '$' + d.total_investment.toFixed(2);

  var badge = document.getElementById('res-badge');
  badge.textContent = d.investment_level;
  badge.className = 'badge badge-' + d.investment_level;
}

/* =========================================================================
   HISTORY
   ========================================================================= */

function renderEvaluationTable(data, tbodyId, emptyId) {
  var tbody = document.getElementById(tbodyId);
  var empty = document.getElementById(emptyId);
  if (!data || data.length === 0) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  tbody.innerHTML = data.map(function (e) {
    return '<tr>' +
      '<td><strong>' + escapeHtml(e.region_name || '—') + '</strong></td>' +
      '<td><span class="badge badge-' + e.investment_level + '">' + e.investment_level + '</span></td>' +
      '<td>$' + Number(e.base_fare).toFixed(2) + '</td>' +
      '<td>' + e.incentive_pct + '%</td>' +
      '<td>$' + Number(e.incentive_amt).toFixed(2) + '</td>' +
      '<td><strong>$' + Number(e.total_investment).toFixed(2) + '</strong></td>' +
      '<td>' + formatDate(e.evaluated_at) + '</td>' +
      '</tr>';
  }).join('');
}

async function loadHistory() {
  var tbody = document.getElementById('history-body');
  var empty = document.getElementById('history-empty');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center"><span class="spinner"></span></td></tr>';
  empty.style.display = 'none';
  try {
    var data = await api('/fleet/history?source=MANUAL&limit=50');
    renderEvaluationTable(data, 'history-body', 'history-empty');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
    empty.style.display = '';
  }
}

async function loadScheduled() {
  var tbody = document.getElementById('scheduled-body');
  var empty = document.getElementById('scheduled-empty');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center"><span class="spinner"></span></td></tr>';
  empty.style.display = 'none';
  try {
    var data = await api('/fleet/history?source=SCHEDULED&limit=50');
    renderEvaluationTable(data, 'scheduled-body', 'scheduled-empty');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
    empty.style.display = '';
  }
}

document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);
document.getElementById('btn-refresh-scheduled').addEventListener('click', loadScheduled);

/* =========================================================================
   REGIONS
   ========================================================================= */

async function loadRegions() {
  var tbody = document.getElementById('regions-body');
  var empty = document.getElementById('regions-empty');
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center"><span class="spinner"></span></td></tr>';
  empty.style.display = 'none';

  try {
    var data = await api('/regions');
    if (!data || data.length === 0) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    tbody.innerHTML = data.map(function (r) {
      return '<tr>' +
        '<td><strong>' + escapeHtml(r.name) + '</strong></td>' +
        '<td>' + r.lat + '</td>' +
        '<td>' + r.lon + '</td>' +
        '<td>' + formatDate(r.created_at) + '</td>' +
        '<td><button class="btn-delete" data-id="' + r.id + '" data-name="' + escapeHtml(r.name) + '" onclick="deleteRegion(this)">Eliminar</button></td>' +
        '</tr>';
    }).join('');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
    empty.style.display = '';
  }
}

document.getElementById('btn-add-region').addEventListener('click', async function () {
  var nameEl = document.getElementById('region-name');
  var latEl = document.getElementById('region-lat');
  var lonEl = document.getElementById('region-lon');

  var name = nameEl.value.trim();
  var latVal = latEl.value;
  var lonVal = lonEl.value;

  // Validate
  var errors = [];
  if (!name) errors.push('Ingresa un nombre para la region');
  if (name.length > 255) errors.push('El nombre no puede exceder 255 caracteres');

  var latErr = validateLat(latVal);
  var lonErr = validateLon(lonVal);
  if (latErr) errors.push('Latitud: ' + latErr);
  if (lonErr) errors.push('Longitud: ' + lonErr);

  if (errors.length > 0) {
    toast(errors[0], true);
    return;
  }

  var btn = document.getElementById('btn-add-region');
  btn.disabled = true;
  btn.textContent = 'Agregando...';

  try {
    await api('/regions', {
      method: 'POST',
      body: JSON.stringify({ name: name, lat: Number(latVal), lon: Number(lonVal) }),
    });
    toast('Region "' + name + '" creada exitosamente');
    nameEl.value = '';
    latEl.value = '';
    lonEl.value = '';
    loadRegions();
    loadRegionDropdown(); // refresh evaluate dropdown too
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Agregar';
  }
});

async function deleteRegion(btnEl) {
  var id = btnEl.dataset.id;
  var name = btnEl.dataset.name;
  if (!confirm('Eliminar la region "' + name + '"? Se eliminaran tambien sus snapshots y evaluaciones.')) {
    return;
  }
  btnEl.disabled = true;
  btnEl.textContent = 'Eliminando...';
  try {
    await api('/regions/' + id, { method: 'DELETE' });
    toast('Region "' + name + '" eliminada');
    loadRegions();
    loadRegionDropdown();
  } catch (e) {
    toast(e.message, true);
    btnEl.disabled = false;
    btnEl.textContent = 'Eliminar';
  }
}

window.deleteRegion = deleteRegion;

/* =========================================================================
   CONFIG
   ========================================================================= */

async function loadConfig() {
  var tbody = document.getElementById('config-body');
  var empty = document.getElementById('config-empty');
  tbody.innerHTML = '<tr><td colspan="4" style="text-align:center"><span class="spinner"></span></td></tr>';
  empty.style.display = 'none';

  try {
    var data = await api('/config/incentive');
    if (!data || data.length === 0) {
      tbody.innerHTML = '';
      empty.style.display = '';
      return;
    }
    tbody.innerHTML = data.map(function (c) {
      return '<tr>' +
        '<td><span class="condition-' + c.condition + '"><strong>' + c.condition + '</strong></span></td>' +
        '<td><input type="number" step="0.01" min="0.01" value="' + c.base_fare + '" ' +
             'id="cfg-fare-' + c.condition + '" class="cfg-input"></td>' +
        '<td><input type="number" step="0.1" min="0" max="100" value="' + c.incentive_pct + '" ' +
             'id="cfg-pct-' + c.condition + '" class="cfg-input cfg-input-sm"></td>' +
        '<td><button class="btn btn-secondary btn-sm" data-condition="' + c.condition + '" ' +
             'onclick="saveConfig(this)">Guardar</button></td>' +
        '</tr>';
    }).join('');
  } catch (e) {
    toast(e.message, true);
    tbody.innerHTML = '';
    empty.style.display = '';
  }
}

async function saveConfig(btnEl) {
  var condition = btnEl.dataset.condition;
  var fareInput = document.getElementById('cfg-fare-' + condition);
  var pctInput = document.getElementById('cfg-pct-' + condition);

  var baseFare = Number(fareInput.value);
  var pct = Number(pctInput.value);

  // Validate
  fareInput.classList.remove('invalid');
  pctInput.classList.remove('invalid');

  if (isNaN(baseFare) || baseFare <= 0) {
    fareInput.classList.add('invalid');
    toast('La tarifa base debe ser mayor a 0', true);
    return;
  }
  if (isNaN(pct) || pct < 0 || pct > 100) {
    pctInput.classList.add('invalid');
    toast('El porcentaje debe estar entre 0 y 100', true);
    return;
  }

  btnEl.disabled = true;
  btnEl.textContent = 'Guardando...';

  try {
    await api('/config/incentive/' + condition, {
      method: 'PUT',
      body: JSON.stringify({ base_fare: baseFare, incentive_pct: pct }),
    });
    toast('Configuracion de ' + condition + ' actualizada');
  } catch (e) {
    toast(e.message, true);
  } finally {
    btnEl.disabled = false;
    btnEl.textContent = 'Guardar';
  }
}

window.saveConfig = saveConfig;

// Create new config
document.getElementById('btn-add-config').addEventListener('click', async function () {
  var condEl = document.getElementById('cfg-new-condition');
  var fareEl = document.getElementById('cfg-new-fare');
  var pctEl = document.getElementById('cfg-new-pct');

  var condition = condEl.value;
  var baseFare = Number(fareEl.value);
  var pct = Number(pctEl.value);

  if (!condition) { toast('Selecciona una condicion climatica', true); return; }
  if (isNaN(baseFare) || baseFare <= 0) { toast('La tarifa base debe ser mayor a 0', true); return; }
  if (isNaN(pct) || pct < 0 || pct > 100) { toast('El porcentaje debe estar entre 0 y 100', true); return; }

  var btn = document.getElementById('btn-add-config');
  btn.disabled = true;
  btn.textContent = 'Agregando...';

  try {
    await api('/config/incentive', {
      method: 'POST',
      body: JSON.stringify({ condition: condition, base_fare: baseFare, incentive_pct: pct }),
    });
    toast('Configuracion de ' + condition + ' creada');
    condEl.value = '';
    fareEl.value = '120.00';
    pctEl.value = '0';
    loadConfig();
  } catch (e) {
    toast(e.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Agregar';
  }
});

/* =========================================================================
   UTILS
   ========================================================================= */

function formatDate(str) {
  if (!str) return '-';
  try {
    var d = new Date(str);
    if (isNaN(d.getTime())) return str;
    return d.toLocaleString();
  } catch (e) {
    return str;
  }
}

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/* === Initial data load === */
loadRegionDropdown();
