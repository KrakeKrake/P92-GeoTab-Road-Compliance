<?php require 'config.php'; ?>
<!DOCTYPE html>
<html>
<head>
<title>Vehicle Config</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: sans-serif; max-width: 700px; margin: 30px auto; padding: 0 16px; color: #222; }
  h2 { margin-bottom: 20px; }
  .row { display: flex; align-items: center; margin-bottom: 14px; gap: 10px; }
  .row label { width: 130px; font-weight: 600; flex-shrink: 0; }
  .row select, .row input[type=number] { flex: 1; padding: 7px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
  .tare-row { align-items: flex-start; }
  .tare-wrap { flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .tare-wrap input { width: 100%; }
  .tare-note { font-size: 12px; color: #888; }
  .tare-reset { font-size: 12px; color: #0066cc; cursor: pointer; text-decoration: underline; display: none; }
  .tare-modified .tare-reset { display: inline; }
  .tare-modified input { border-color: #f90; background: #fffbe6; }
  .info-box { background: #f4f6f8; border: 1px solid #dde; border-radius: 6px; padding: 14px 16px; margin-bottom: 18px; font-size: 13px; }
  .info-box table { width: 100%; border-collapse: collapse; }
  .info-box td { padding: 3px 8px 3px 0; }
  .info-box td:first-child { font-weight: 600; width: 110px; }
  .mass-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  .mass-table th, .mass-table td { border: 1px solid #ccc; padding: 5px 10px; text-align: center; font-size: 13px; }
  .mass-table th { background: #e8ecf0; }
  .groups-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }
  .groups-table th, .groups-table td { border: 1px solid #ddd; padding: 4px 10px; }
  .groups-table th { background: #eef0f3; }
  button { padding: 9px 24px; background: #1a5dc8; color: #fff; border: none; border-radius: 4px; font-size: 15px; cursor: pointer; }
  button:hover { background: #154aaa; }
  #result { margin-top: 16px; font-size: 16px; font-weight: 600; padding: 12px 16px; border-radius: 5px; display: none; }
  .good { background: #e8f7ec; color: #1a7a3a; border: 1px solid #a3d9b1; }
  .bad  { background: #fdecea; color: #c0392b; border: 1px solid #f5a8a2; }
  .warn { background: #fff8e1; color: #7a5900; border: 1px solid #ffe082; }
</style>
</head>
<body>

<h2>Vehicle Setup</h2>

<div class="row">
  <label>Class</label>
  <select id="class">
    <option value="2">Class 2</option>
    <option value="3">Class 3</option>
  </select>
</div>

<div class="row">
  <label>Type</label>
  <select id="type"></select>
</div>

<div class="row">
  <label>Configuration</label>
  <select id="config"></select>
</div>

<div id="config-info" class="info-box" style="display:none"></div>

<div class="row tare-row" id="tare-row">
  <label>Tare (kg)</label>
  <div class="tare-wrap" id="tare-wrap">
    <input id="tare" type="number" min="0" step="1">
    <span class="tare-note">Auto-filled from configuration. Edit to override locally.</span>
    <span class="tare-reset" id="tare-reset" onclick="resetTare()">↩ Reset to default</span>
  </div>
</div>

<div class="row">
  <label>Payload (kg)</label>
  <input id="payload" type="number" min="0" step="1">
</div>

<button onclick="check()">Check</button>

<div id="result"></div>

<script>
// Local tare overrides stored by axle_id
const tareOverrides = {};
let defaultTare = null;
let currentAxleId = null;

// ---- LOAD TYPES ----
function loadTypes() {
    const classId = document.getElementById('class').value;
    fetch('get_types.php?class_id=' + classId)
    .then(r => r.json())
    .then(data => {
        const sel = document.getElementById('type');
        sel.innerHTML = '';
        data.forEach(d => {
            sel.innerHTML += `<option value="${d.vehicle_id}">${d.name}</option>`;
        });
        if (data.length > 0) loadConfigs();
        else {
            document.getElementById('config').innerHTML = '';
            clearInfo();
        }
    });
}

// ---- LOAD CONFIGS ----
function loadConfigs() {
    const vehicleId = document.getElementById('type').value;
    if (!vehicleId) return;
    fetch('get_configs.php?vehicle_id=' + vehicleId)
    .then(r => r.json())
    .then(data => {
        const sel = document.getElementById('config');
        sel.innerHTML = '';
        data.forEach(d => {
            sel.innerHTML += `<option value="${d.axle_id}">${d.config_name}</option>`;
        });
        if (data.length > 0) loadDetails();
        else clearInfo();
    });
}

// ---- LOAD DETAILS ----
function loadDetails() {
    const axleId = document.getElementById('config').value;
    if (!axleId) return;
    currentAxleId = axleId;

    fetch('get_config_details.php?axle_id=' + axleId)
    .then(r => r.json())
    .then(data => {
        defaultTare = data.tare;

        // Tare: use local override if set, else DB value
        const tareInput = document.getElementById('tare');
        const tareWrap  = document.getElementById('tare-wrap');
        if (tareOverrides[axleId] !== undefined) {
            tareInput.value = tareOverrides[axleId];
            tareWrap.classList.add('tare-modified');
        } else {
            tareInput.value = data.tare ?? '';
            tareWrap.classList.remove('tare-modified');
        }

        // Info box
        const box = document.getElementById('config-info');
        box.style.display = 'block';

        let massRows = '';
        if (data.gml) massRows += `<tr><th>GML</th><td>${data.gml} t</td></tr>`;
        if (data.cml) massRows += `<tr><th>CML</th><td>${data.cml} t</td></tr>`;
        if (data.hml) massRows += `<tr><th>HML</th><td>${data.hml} t</td></tr>`;

        let groupRows = '';
        if (data.groups && data.groups.length > 0) {
            groupRows = `<br><strong>Axle Groups</strong>
            <table class="groups-table">
              <tr><th>Group</th><th>Limit (kg)</th></tr>
              ${data.groups.map(g => `<tr><td>${g.group_name}</td><td>${Number(g.group_limit).toLocaleString()}</td></tr>`).join('')}
            </table>`;
        }

        box.innerHTML = `
          <table>
            <tr><td>Axles</td><td>${data.axle_count ?? '—'}</td></tr>
            <tr><td>Max Length</td><td>${data.max_length ? data.max_length + ' m' : '—'}</td></tr>
          </table>
          <br>
          <strong>Mass Limits</strong>
          <table class="mass-table">
            <tr><th>GML</th><th>CML</th><th>HML</th></tr>
            <tr>
              <td>${data.gml ? data.gml + ' t' : '—'}</td>
              <td>${data.cml ? data.cml + ' t' : '—'}</td>
              <td>${data.hml ? data.hml + ' t' : '—'}</td>
            </tr>
          </table>
          ${groupRows}`;

        // Store limits on config element for check()
        const configSel = document.getElementById('config');
        configSel.dataset.gml = data.gml ?? '';
        configSel.dataset.cml = data.cml ?? '';
        configSel.dataset.hml = data.hml ?? '';

        document.getElementById('result').style.display = 'none';
    });
}

// ---- TARE OVERRIDE ----
document.getElementById('tare').addEventListener('input', function() {
    if (!currentAxleId) return;
    const val = parseFloat(this.value);
    const tareWrap = document.getElementById('tare-wrap');
    if (!isNaN(val) && val !== defaultTare) {
        tareOverrides[currentAxleId] = val;
        tareWrap.classList.add('tare-modified');
    } else {
        delete tareOverrides[currentAxleId];
        tareWrap.classList.remove('tare-modified');
    }
});

function resetTare() {
    if (!currentAxleId) return;
    delete tareOverrides[currentAxleId];
    document.getElementById('tare').value = defaultTare ?? '';
    document.getElementById('tare-wrap').classList.remove('tare-modified');
}

// ---- CHECK ----
function check() {
    const tare    = parseFloat(document.getElementById('tare').value);
    const payload = parseFloat(document.getElementById('payload').value);
    const result  = document.getElementById('result');
    const config  = document.getElementById('config');
    const gml     = parseFloat(config.dataset.gml) * 1000; // tonnes -> kg
    const cml     = parseFloat(config.dataset.cml) * 1000;
    const hml     = parseFloat(config.dataset.hml) * 1000;

    result.style.display = 'block';

    if (isNaN(tare)) {
        result.className = 'warn'; result.textContent = 'Enter a tare weight.'; return;
    }
    if (isNaN(payload) || payload < 0) {
        result.className = 'warn'; result.textContent = 'Enter a valid payload.'; return;
    }
    if (isNaN(gml)) {
        result.className = 'warn'; result.textContent = 'No mass limit data for this configuration.'; return;
    }

    const gross = tare + payload;
    const grossT = (gross / 1000).toFixed(2);
    const gmlT   = (gml  / 1000).toFixed(1);

    if (gross <= gml) {
        const headroom = ((gml - gross) / 1000).toFixed(2);
        result.className = 'good';
        result.textContent = `✔ PASS — Gross ${grossT} t is within GML of ${gmlT} t (${headroom} t headroom).`;
    } else {
        const over = ((gross - gml) / 1000).toFixed(2);
        result.className = 'bad';
        result.textContent = `✘ FAIL — Gross ${grossT} t exceeds GML of ${gmlT} t by ${over} t.`;
    }
}

// ---- CLEAR INFO ----
function clearInfo() {
    document.getElementById('config-info').style.display = 'none';
    document.getElementById('tare').value = '';
    document.getElementById('result').style.display = 'none';
}

// ---- EVENT LISTENERS ----
document.getElementById('class').addEventListener('change', loadTypes);
document.getElementById('type').addEventListener('change', loadConfigs);
document.getElementById('config').addEventListener('change', loadDetails);

// INIT
loadTypes();
</script>
</body>
</html>