// ==========================================================================
// AI Automation Hub - Frontend Controller
// Enterprise Web Dashboard & Realtime Engine
// ==========================================================================

let allModules = [];
let allLogs = [];
let currentCategory = 'all';
let currentStatusFilter = 'all';
let currentActiveModule = null;

// --- Initialize App ---
function initHub() {
  console.log("⚡ AI Automation Hub inicializálása...");
  loadStats();
  loadModules();
  setupGlobalEvents();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initHub);
} else {
  initHub();
}

function setupGlobalEvents() {
  // ESC billentyű modal bezárás
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal('modal-wizard');
      closeModal('modal-logs');
      closeModal('modal-log-detail');
    }
  });
}

// --- Toast Notifications ---
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  else if (type === 'error') icon = '❌';
  else if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span>${icon}</span>
      <span>${message}</span>
    </div>
    <button style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:14px;" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }
  }, duration);
}

// --- Load Quick Stats ---
async function loadStats() {
  try {
    const res = await fetch('/api/v1/stats');
    if (!res.ok) return;
    const data = await res.json();
    const runsToday = document.getElementById('stat-runs-today');
    const successRate = document.getElementById('stat-success-rate');
    if (runsToday) runsToday.innerText = data.runs_today || 0;
    if (successRate) successRate.innerText = (data.success_rate !== undefined ? data.success_rate : 100) + '%';
  } catch (err) {
    console.error("Hiba a statisztikák lekérésekor:", err);
  }
}

// --- Load Modules ---
async function loadModules() {
  const container = document.getElementById('modules-grid');
  try {
    const res = await fetch('/api/v1/modules');
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    allModules = await res.json();

    // Számlálók frissítése
    const statTotal = document.getElementById('stat-total-modules');
    const statActive = document.getElementById('stat-active-modules');
    const countAll = document.getElementById('count-all');

    if (statTotal) statTotal.innerText = allModules.length;
    const activeCount = allModules.filter(m => m.status === 'active').length;
    if (statActive) statActive.innerText = activeCount;
    if (countAll) countAll.innerText = allModules.length;

    // Kategória számlálók
    const catCounts = { altalanos: 0, szolgaltatok: 0, kereskedok: 0, webshopok: 0, muszaki: 0 };
    allModules.forEach(m => {
      if (catCounts[m.category] !== undefined) {
        catCounts[m.category]++;
      }
    });

    for (const [cat, cnt] of Object.entries(catCounts)) {
      const el = document.getElementById(`count-${cat}`);
      if (el) el.innerText = cnt;
    }

    renderModules();
  } catch (err) {
    if (container) {
      container.innerHTML = `
        <div class="loading-state text-danger">
          <p>⚠️ Nem sikerült kapcsolódni a Hub szerverhez: ${err.message}</p>
          <button class="btn btn-outline btn-sm" onclick="loadModules()" style="margin-top: 12px;">Újrapróbálás</button>
        </div>
      `;
    }
  }
}

// --- Render Modules Grid ---
function renderModules() {
  const container = document.getElementById('modules-grid');
  if (!container) return;

  const searchInput = document.getElementById('search-input');
  const search = (searchInput ? searchInput.value : '').toLowerCase().trim();

  // Clear gomb láthatósága
  const clearBtn = document.getElementById('search-clear-btn');
  if (clearBtn) {
    clearBtn.style.display = search ? 'block' : 'none';
  }

  const filtered = allModules.filter(m => {
    // Kategória szűrés
    const matchesCat = (currentCategory === 'all' || m.category === currentCategory);
    
    // Állapot szűrés
    let matchesStatus = true;
    if (currentStatusFilter === 'active') {
      matchesStatus = (m.status === 'active');
    } else if (currentStatusFilter === 'needs_setup') {
      matchesStatus = (m.status === 'needs_setup');
    }

    // Keresés
    const matchesSearch = (!search || 
      m.title.toLowerCase().includes(search) || 
      m.id.toLowerCase().includes(search) || 
      (m.description && m.description.toLowerCase().includes(search))
    );

    return matchesCat && matchesStatus && matchesSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="loading-state">
        <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
        <p>Nem található a szűrésnek megfelelő modul.</p>
        <button class="btn btn-outline btn-sm" onclick="resetFilters()" style="margin-top: 12px;">Szűrők törlése</button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(m => {
    const webhookUrl = `${window.location.origin}/api/v1/webhook/${m.id}`;
    const isActive = m.config && m.config._is_active !== false;

    return `
      <div class="module-card" id="card-${m.id}">
        <div>
          <div class="card-header">
            <div class="module-icon-title">
              <span class="module-icon" role="img" aria-label="Modul ikon">${m.icon || '⚡'}</span>
              <div class="module-title-wrapper">
                <div class="module-title" title="${m.title}">${m.title}</div>
                <div class="module-category-tag">${m.category_name}</div>
              </div>
            </div>
            <div class="card-status-area">
              <label class="switch card-toggle" title="Modul aktiválása / inaktiválása">
                <input type="checkbox" ${isActive ? 'checked' : ''} onchange="toggleModuleActive('${m.id}', event)">
                <span class="slider round"></span>
              </label>
              <span class="badge badge-${m.status}">${m.status_text}</span>
            </div>
          </div>

          <p class="card-desc" title="${m.description || ''}">${m.description || 'Nincs részletes leírás.'}</p>

          <div class="webhook-preview" title="Kattintson a webhook URL másolásához" onclick="copyWebhookUrl('${webhookUrl}', this)">
            <span class="webhook-preview-text">🔗 /api/v1/webhook/${m.id}</span>
            <button class="btn-copy-sm" type="button">Másolás</button>
          </div>
        </div>

        <div class="card-footer">
          <button class="btn btn-primary" onclick="openSetupWizard('${m.id}')" title="Modul beállításai és bekötési útmutató">
            ⚙️ Beállítás & Bekötés
          </button>
          <button class="btn btn-outline" onclick="quickTestModule('${m.id}')" title="Gyors teszt futtatása mintával">
            🧪 Teszt
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// --- Category & Status Filter Handlers ---
function setCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll('.category-tabs .tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-category') === cat);
  });
  renderModules();
}

function setStatusFilter(status) {
  currentStatusFilter = status;
  document.querySelectorAll('.filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-status') === status);
  });
  renderModules();
}

function filterModules() {
  renderModules();
}

function clearSearch() {
  const input = document.getElementById('search-input');
  if (input) {
    input.value = '';
    input.focus();
  }
  renderModules();
}

function resetFilters() {
  currentCategory = 'all';
  currentStatusFilter = 'all';
  const input = document.getElementById('search-input');
  if (input) input.value = '';
  document.querySelectorAll('.category-tabs .tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-category') === 'all');
  });
  document.querySelectorAll('.filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-status') === 'all');
  });
  renderModules();
}

// --- Direct Card Active Toggle ---
async function toggleModuleActive(moduleId, event) {
  event.stopPropagation();
  try {
    const res = await fetch(`/api/v1/modules/${moduleId}/toggle`, {
      method: 'POST'
    });
    const result = await res.json();
    if (result.status === 'success') {
      const stateText = result.is_active ? 'bekapcsolva' : 'kikapcsolva';
      showToast(`A(z) '${moduleId}' modul sikeresen ${stateText}!`, 'success');
      
      // Frissítjük a memóriában lévő modult
      const mod = allModules.find(m => m.id === moduleId);
      if (mod) {
        if (!mod.config) mod.config = {};
        mod.config._is_active = result.is_active;
        mod.status = result.is_active ? 'active' : 'disabled';
        mod.status_text = result.is_active ? 'Aktív & Üzemkész' : 'Kikapcsolva';
      }
      loadModules();
    } else {
      showToast(`Hiba a modul átkapcsolásakor: ${result.error}`, 'error');
    }
  } catch (err) {
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

// --- Copy Webhook & Text Helpers ---
function copyWebhookUrl(url, el) {
  navigator.clipboard.writeText(url).then(() => {
    const copyBtn = el.querySelector('.btn-copy-sm') || el;
    const orig = copyBtn.innerText;
    copyBtn.innerText = '✓ Másolva!';
    copyBtn.style.background = '#10b981';
    copyBtn.style.borderColor = '#10b981';
    showToast('Webhook URL a vágólapra másolva!', 'success', 2000);
    setTimeout(() => {
      copyBtn.innerText = orig;
      copyBtn.style.background = '';
      copyBtn.style.borderColor = '';
    }, 1500);
  }).catch(() => {
    prompt("Másolja ki a Webhook URL-t:", url);
  });
}

function copyCurrentWebhook(btn) {
  if (!currentActiveModule) return;
  const url = `${window.location.origin}/api/v1/webhook/${currentActiveModule.id}`;
  navigator.clipboard.writeText(url).then(() => {
    const orig = btn.innerText;
    btn.innerText = '✓ Másolva!';
    showToast('Dedikált Webhook URL kimásolva!', 'success', 2000);
    setTimeout(() => { btn.innerText = orig; }, 1500);
  }).catch(() => {
    prompt("Másolja ki a Webhook URL-t:", url);
  });
}

function copyTestOutput(btn) {
  const viewer = document.getElementById('test-output-viewer');
  if (!viewer) return;
  navigator.clipboard.writeText(viewer.innerText).then(() => {
    const orig = btn.innerText;
    btn.innerText = '✓ Másolva!';
    showToast('Teszt válasz a vágólapra másolva!', 'success', 2000);
    setTimeout(() => { btn.innerText = orig; }, 1500);
  });
}

// --- Setup Wizard Modal ---
function openSetupWizard(moduleId) {
  const m = allModules.find(item => item.id === moduleId);
  if (!m) return;
  currentActiveModule = m;

  document.getElementById('modal-module-icon').innerText = m.icon || '⚡';
  document.getElementById('modal-module-title').innerText = m.title;
  document.getElementById('modal-module-id-badge').innerText = m.id;
  
  const statusBadge = document.getElementById('modal-module-status');
  statusBadge.className = `badge badge-${m.status}`;
  statusBadge.innerText = m.status_text;

  // Webhook URL
  document.getElementById('modal-webhook-url').innerText = `${window.location.origin}/api/v1/webhook/${m.id}`;

  // Markdown README
  const readmeContainer = document.getElementById('modal-readme-content');
  if (m.readme && window.marked) {
    readmeContainer.innerHTML = marked.parse(m.readme);
  } else {
    readmeContainer.innerHTML = `<p>${m.description || 'Nincs részletes dokumentáció.'}</p>`;
  }

  // Dinamikus konfigurációs mezők kirajzolása
  renderDynamicConfigForm(m);

  // Teszt fül előkészítése
  const payloadBox = document.getElementById('test-payload-input');
  if (payloadBox) {
    payloadBox.value = JSON.stringify(m.test_payload || {}, null, 2);
  }
  const viewer = document.getElementById('test-output-viewer');
  if (viewer) viewer.innerText = 'Kattintson a "Teszt Futtatása Most" gombra a modul meghívásához...';
  const durationBadge = document.getElementById('test-duration-badge');
  if (durationBadge) durationBadge.innerText = '-';

  switchModalTab('tab-guide');
  const modal = document.getElementById('modal-wizard');
  if (modal) modal.style.display = 'flex';
}

function quickTestModule(moduleId) {
  openSetupWizard(moduleId);
  switchModalTab('tab-test');
}

// --- Dynamic Config Form Renderer ---
function renderDynamicConfigForm(m) {
  const container = document.getElementById('dynamic-config-fields');
  if (!container) return;

  const schema = m.schema || {};
  const props = schema.properties || {};
  const saved = m.config || {};
  const fieldCountBadge = document.getElementById('config-field-count');

  const keys = Object.keys(props);
  if (fieldCountBadge) {
    fieldCountBadge.innerText = `${keys.length} beállítható mező`;
  }

  // Modul be/ki kapcsoló állapot
  const activeCheckbox = document.getElementById('config-is-active');
  if (activeCheckbox) {
    activeCheckbox.checked = (saved._is_active !== false);
  }

  if (keys.length === 0) {
    container.innerHTML = `
      <div style="padding: 24px; text-align: center; color: var(--text-muted);">
        <p>ℹ️ Ehhez a modulhoz nincs szükség külön paraméterezésre, azonnal használható.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = keys.map(key => {
    const p = props[key];
    const val = saved[key] !== undefined ? saved[key] : (p.default !== undefined ? p.default : '');
    const isRequired = (schema.required || []).includes(key);

    let inputHtml = '';

    // 1. Enum lista (Select)
    if (p.enum && Array.isArray(p.enum)) {
      inputHtml = `
        <select name="${key}" class="form-control" data-type="string">
          ${p.enum.map(opt => `<option value="${opt}" ${opt === val ? 'selected' : ''}>${opt}</option>`).join('')}
        </select>
      `;
    }
    // 2. Boolean (Kapcsoló switch)
    else if (p.type === 'boolean') {
      const checked = (val === true || val === 'true');
      inputHtml = `
        <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
          <label class="switch">
            <input type="checkbox" name="${key}" data-type="boolean" ${checked ? 'checked' : ''}>
            <span class="slider round"></span>
          </label>
          <span style="font-size: 12.5px; color: var(--text-muted);">${checked ? 'Bekapcsolva' : 'Kikapcsolva'}</span>
        </div>
      `;
    }
    // 3. Integer / Number
    else if (p.type === 'integer' || p.type === 'number') {
      const step = p.type === 'integer' ? '1' : 'any';
      inputHtml = `
        <input type="number" step="${step}" name="${key}" class="form-control" value="${val}" data-type="${p.type}" placeholder="${p.default !== undefined ? p.default : ''}">
      `;
    }
    // 4. Jelszó / API Kulcs formátum
    else if (p.format === 'password') {
      inputHtml = `
        <div class="password-wrapper">
          <input type="password" name="${key}" class="form-control" value="${val}" placeholder="sk-... vagy kulcs" data-type="string">
          <button type="button" class="btn-toggle-eye" onclick="togglePasswordVisibility(this)" title="Jelszó mutatása/elrejtése">👁️</button>
        </div>
      `;
    }
    // 5. Textarea formátum
    else if (p.format === 'textarea') {
      inputHtml = `
        <textarea name="${key}" class="form-control" rows="4" data-type="string" placeholder="${p.default || ''}">${val}</textarea>
      `;
    }
    // 6. Array (Lista)
    else if (p.type === 'array') {
      let arrayStr = '';
      if (Array.isArray(val)) {
        arrayStr = val.join(', ');
      } else if (typeof val === 'string') {
        arrayStr = val;
      }
      inputHtml = `
        <input type="text" name="${key}" class="form-control" value="${arrayStr}" data-type="array" placeholder="elem1, elem2, elem3 (vesszővel elválasztva)">
      `;
    }
    // 7. Object (JSON)
    else if (p.type === 'object') {
      const objStr = typeof val === 'object' ? JSON.stringify(val, null, 2) : val;
      inputHtml = `
        <textarea name="${key}" class="form-control code-textarea" rows="4" data-type="object" spellcheck="false">${objStr}</textarea>
      `;
    }
    // 8. Alapértelmezett String input
    else {
      inputHtml = `
        <input type="text" name="${key}" class="form-control" value="${val}" data-type="string" placeholder="${p.default !== undefined ? p.default : ''}">
      `;
    }

    return `
      <div class="form-group">
        <label for="field-${key}">
          ${p.title || key} ${isRequired ? '<span class="text-danger" title="Kötelező mező">*</span>' : ''}
        </label>
        ${inputHtml}
        ${p.description ? `<div class="form-hint">${p.description}</div>` : ''}
      </div>
    `;
  }).join('');
}

function togglePasswordVisibility(btn) {
  const input = btn.previousElementSibling;
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerText = '🔒';
  } else {
    input.type = 'password';
    btn.innerText = '👁️';
  }
}

// --- Save Config with Type-Safety ---
async function saveCurrentConfig(event) {
  event.preventDefault();
  if (!currentActiveModule) return;

  const form = document.getElementById('module-config-form');
  const schema = currentActiveModule.schema || {};
  const props = schema.properties || {};
  const required = schema.required || [];
  const config = {};
  const missing = [];

  // Típushelyes kiolvasás
  for (const [key, p] of Object.entries(props)) {
    const el = form.elements[key];
    if (!el) continue;

    if (p.type === 'boolean') {
      config[key] = el.checked;
    } else if (p.type === 'integer') {
      const val = el.value.trim();
      config[key] = val !== '' ? parseInt(val, 10) : (p.default !== undefined ? p.default : null);
    } else if (p.type === 'number') {
      const val = el.value.trim();
      config[key] = val !== '' ? parseFloat(val) : (p.default !== undefined ? p.default : null);
    } else if (p.type === 'array') {
      const raw = el.value.trim();
      if (raw.startsWith('[') && raw.endsWith(']')) {
        try {
          config[key] = JSON.parse(raw);
        } catch (_) {
          config[key] = raw.split(',').map(s => s.trim()).filter(Boolean);
        }
      } else {
        config[key] = raw ? raw.split(',').map(s => s.trim()).filter(Boolean) : [];
      }
    } else if (p.type === 'object') {
      try {
        config[key] = el.value.trim() ? JSON.parse(el.value.trim()) : {};
      } catch (e) {
        showToast(`Érvénytelen JSON formátum a(z) '${p.title || key}' mezőben!`, 'error');
        return;
      }
    } else {
      config[key] = el.value !== undefined ? el.value.trim() : '';
    }

    // Kötelező ellenőrzés
    if (required.includes(key)) {
      const v = config[key];
      if (v === '' || v === null || v === undefined) {
        missing.push(p.title || key);
      }
    }
  }

  if (missing.length > 0) {
    showToast(`Kérjük töltse ki a kötelező mezőket: ${missing.join(', ')}`, 'warning');
    return;
  }

  const isActive = document.getElementById('config-is-active').checked;
  const btn = document.getElementById('btn-save-config');
  btn.innerText = 'Mentés... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch(`/api/v1/modules/${currentActiveModule.id}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config, is_active: isActive })
    });

    const result = await res.json();
    btn.innerText = '💾 Beállítások Mentése';
    btn.disabled = false;

    if (result.status === 'success') {
      showToast('A modul beállításai sikeresen elmentve!', 'success');
      
      // Frissítjük a modul adatait lokálisan
      currentActiveModule.config = { ...currentActiveModule.config, ...config, _is_active: isActive };
      currentActiveModule.status = isActive ? 'active' : 'disabled';
      currentActiveModule.status_text = isActive ? 'Aktív & Üzemkész' : 'Kikapcsolva';

      closeModal('modal-wizard');
      loadModules();
      loadStats();
    } else {
      showToast(`Hiba a mentés során: ${result.error}`, 'error');
    }
  } catch (err) {
    btn.innerText = '💾 Beállítások Mentése';
    btn.disabled = false;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

// --- Live Test Execution ---
function resetDefaultPayload() {
  if (currentActiveModule && currentActiveModule.test_payload) {
    document.getElementById('test-payload-input').value = JSON.stringify(currentActiveModule.test_payload, null, 2);
    showToast('Alapértelmezett minta payload betöltve.', 'info', 1500);
  }
}

async function runLiveTest() {
  if (!currentActiveModule) return;

  const btn = document.getElementById('btn-run-test');
  const viewer = document.getElementById('test-output-viewer');
  const durationBadge = document.getElementById('test-duration-badge');

  let payload = {};
  try {
    const raw = document.getElementById('test-payload-input').value.trim();
    payload = raw ? JSON.parse(raw) : {};
  } catch (err) {
    showToast("Érvénytelen JSON formátum a bemeneti mezőben!", 'error');
    return;
  }

  btn.innerText = '⏳ Futtatás folyamatban...';
  btn.disabled = true;
  viewer.innerText = 'Kapcsolódás a modulhoz és végrehajtás...';
  viewer.style.color = '#38bdf8';

  try {
    const res = await fetch(`/api/v1/modules/${currentActiveModule.id}/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    btn.innerText = '⚡ Teszt Futtatása Most';
    btn.disabled = false;

    if (data.duration_ms !== undefined) {
      durationBadge.innerText = `${data.duration_ms} ms`;
    }

    if (data.status === 'success') {
      viewer.style.color = '#a7f3d0';
      showToast(`Teszt sikeresen lefutott (${data.duration_ms} ms)!`, 'success', 2500);
    } else {
      viewer.style.color = '#fca5a5';
      showToast(`Teszt végrehajtási hiba történt!`, 'error', 3500);
    }

    viewer.innerText = JSON.stringify(data, null, 2);
    loadStats();
  } catch (err) {
    btn.innerText = '⚡ Teszt Futtatása Most';
    btn.disabled = false;
    viewer.style.color = '#fca5a5';
    viewer.innerText = `Hálózati hiba a hívás során: ${err.message}`;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

// --- Modal Tabs & Controls ---
function switchModalTab(tabId) {
  document.querySelectorAll('.modal-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.modal-tab-content').forEach(c => c.classList.remove('active'));

  const activeBtn = document.getElementById(`m${tabId}`) || event?.target;
  if (activeBtn && activeBtn.classList) activeBtn.classList.add('active');

  const activeContent = document.getElementById(tabId);
  if (activeContent) activeContent.classList.add('active');
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.style.display = 'none';
}

function handleOverlayClick(event, modalId) {
  if (event.target.id === modalId) {
    closeModal(modalId);
  }
}

// --- System Logs Modal ---
async function openLogsModal() {
  const modal = document.getElementById('modal-logs');
  if (!modal) return;
  modal.style.display = 'flex';

  const tbody = document.getElementById('logs-table-body');
  tbody.innerHTML = `<tr><td colspan="5" class="text-center">Naplózott események lekérése...</td></tr>`;

  try {
    const res = await fetch('/api/v1/logs?limit=50');
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    allLogs = await res.json();
    renderLogsTable(allLogs);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-danger text-center">Hiba a naplók betöltésekor: ${err.message}</td></tr>`;
  }
}

function renderLogsTable(logs) {
  const tbody = document.getElementById('logs-table-body');
  if (!tbody) return;

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Még nincs rögzített futási naplóesemény.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map((l, idx) => {
    const isSuccess = l.status === 'success';
    const isSkipped = l.status === 'skipped';
    let badgeClass = 'badge-active';
    if (!isSuccess && !isSkipped) badgeClass = 'badge-disabled';
    else if (isSkipped) badgeClass = 'badge-needs_setup';

    const dateStr = l.timestamp ? new Date(l.timestamp).toLocaleTimeString('hu-HU') : '-';

    return `
      <tr>
        <td><code>${dateStr}</code></td>
        <td><strong>${l.module_id}</strong></td>
        <td><span class="badge ${badgeClass}">${l.status.toUpperCase()}</span></td>
        <td><code>${l.duration_ms} ms</code></td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="openLogDetailModal(${idx})">
            Megtekintés 🔍
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function filterLogsTable() {
  const input = document.getElementById('logs-search-input');
  const q = (input ? input.value : '').toLowerCase().trim();
  if (!q) {
    renderLogsTable(allLogs);
    return;
  }
  const filtered = allLogs.filter(l => 
    (l.module_id && l.module_id.toLowerCase().includes(q)) ||
    (l.status && l.status.toLowerCase().includes(q))
  );
  renderLogsTable(filtered);
}

function openLogDetailModal(idx) {
  const log = allLogs[idx];
  if (!log) return;
  const viewer = document.getElementById('log-detail-viewer');
  if (viewer) {
    viewer.innerText = JSON.stringify(log, null, 2);
  }
  const modal = document.getElementById('modal-log-detail');
  if (modal) modal.style.display = 'flex';
}