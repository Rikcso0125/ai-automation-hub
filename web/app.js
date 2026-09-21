// ==========================================================================
// AI Automation Hub - Frontend Controller
// Enterprise Web Dashboard & Realtime Engine
// ==========================================================================

let allModules = [];
let allLogs = [];
let allAdminClients = [];
let currentCategory = 'all';
let currentStatusFilter = 'all';
let currentActiveModule = null;

// Multi-tenant Auth & Tenant State
let authToken = localStorage.getItem('hub_auth_token') || null;
let currentUser = null;
let activeTenant = null; // Set when Super Admin enters a client's environment
let selectedPresetKey = 'gmail';

// --- Auth Headers Helper ---
function getAuthHeaders(includeJson = true) {
  const headers = {};
  if (includeJson) headers['Content-Type'] = 'application/json';
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
  return headers;
}

// --- Initialize App ---
async function initHub() {
  console.log("⚡ AI Automation Hub inicializálása...");
  await checkAuthStatus();
  checkOAuthRedirectParams();
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
      closeModal('modal-auth');
      closeModal('modal-integrations');
      closeModal('modal-admin-clients');
      closeModal('modal-admin-client-details');
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
    let url = '/api/v1/modules';
    if (activeTenant) {
      url += `?client_id=${activeTenant.id}`;
    }
    const res = await fetch(url, { headers: getAuthHeaders(false) });
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
    let url = `/api/v1/modules/${moduleId}/toggle`;
    if (activeTenant) {
      url += `?client_id=${activeTenant.id}`;
    }
    const res = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(true)
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
    let url = `/api/v1/modules/${currentActiveModule.id}/config`;
    if (activeTenant) {
      url += `?client_id=${activeTenant.id}`;
    }
    const res = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(true),
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
      showToast(`Hiba a mentés során: ${result.error || result.detail || 'Ismeretlen hiba'}`, 'error');
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
    let url = `/api/v1/modules/${currentActiveModule.id}/test`;
    if (activeTenant) {
      url += `?client_id=${activeTenant.id}`;
    }
    const res = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(true),
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

// ==========================================================================
// Multi-Tenant User System, Integrations Vault & Super Admin Controller
// ==========================================================================

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// --- Auth State & Navbar Management ---
async function checkAuthStatus() {
  if (!authToken) {
    currentUser = null;
    renderUserNavbar();
    return;
  }
  try {
    const res = await fetch('/api/v1/auth/me', {
      headers: getAuthHeaders(false)
    });
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        currentUser = data.user;
      } else {
        currentUser = null;
        authToken = null;
        localStorage.removeItem('hub_auth_token');
      }
    } else {
      currentUser = null;
      authToken = null;
      localStorage.removeItem('hub_auth_token');
    }
  } catch (e) {
    console.warn("Auth check failed:", e);
    currentUser = null;
  }
  renderUserNavbar();
}

function renderUserNavbar() {
  const container = document.getElementById('nav-user-area');
  if (!container) return;

  if (!currentUser) {
    container.innerHTML = `
      <button class="btn btn-primary btn-sm" onclick="openAuthModal('login')">
        <span class="icon">👤</span> <span class="action-text">Belépés / Regisztráció</span>
      </button>
    `;
    return;
  }

  if (currentUser.role === 'superadmin') {
    container.innerHTML = `
      <div class="user-badge admin" title="Szuper Adminisztrátori Fiók">
        <span class="user-role-badge admin">👑 Admin</span>
        <strong>${escapeHtml(currentUser.email)}</strong>
      </div>
      <button class="btn btn-primary btn-sm" onclick="openAdminClientsModal()">
        <span class="icon">👥</span> <span class="action-text">Ügyfelek</span> (<span id="nav-client-count">...</span>)
      </button>
      <button class="btn btn-outline btn-sm" onclick="logoutUser()" title="Kijelentkezés">
        <span class="icon">🚪</span>
      </button>
    `;
    refreshAdminClientsCount();
  } else {
    const displayName = currentUser.company_name || currentUser.full_name || currentUser.email;
    container.innerHTML = `
      <div class="user-badge" title="Bejelentkezett vállalati fiók">
        <span class="user-role-badge">Ügyfél</span>
        <strong>${escapeHtml(displayName)}</strong>
      </div>
      <button class="btn btn-outline btn-sm btn-vault" onclick="openIntegrationsModal()">
        <span class="icon">🔗</span> <span class="action-text">Hozzáféréseim & Integrációk</span>
      </button>
      <button class="btn btn-outline btn-sm" onclick="logoutUser()" title="Kijelentkezés">
        <span class="icon">🚪</span>
      </button>
    `;
  }
}

async function refreshAdminClientsCount() {
  if (!currentUser || currentUser.role !== 'superadmin') return;
  try {
    const res = await fetch('/api/v1/admin/clients', {
      headers: getAuthHeaders(false)
    });
    if (res.ok) {
      const data = await res.json();
      allAdminClients = data.clients || [];
      const el = document.getElementById('nav-client-count');
      if (el) el.innerText = allAdminClients.length;
    }
  } catch (_) {}
}

// --- Auth Modal & Form Handlers ---
function openAuthModal(tab = 'login') {
  switchAuthTab(tab);
  const modal = document.getElementById('modal-auth');
  if (modal) modal.style.display = 'flex';
}

function switchAuthTab(tab) {
  const tabLogin = document.getElementById('tab-auth-login');
  const tabReg = document.getElementById('tab-auth-register');
  const formLogin = document.getElementById('form-auth-login');
  const formReg = document.getElementById('form-auth-register');
  const title = document.getElementById('auth-modal-title');

  if (tab === 'login') {
    if (tabLogin) tabLogin.classList.add('active');
    if (tabReg) tabReg.classList.remove('active');
    if (formLogin) formLogin.style.display = 'block';
    if (formReg) formReg.style.display = 'none';
    if (title) title.innerText = '🔐 Ügyfél Belépés & Szuper Admin';
    setTimeout(() => { document.getElementById('login-email')?.focus(); }, 100);
  } else {
    if (tabLogin) tabLogin.classList.remove('active');
    if (tabReg) tabReg.classList.add('active');
    if (formLogin) formLogin.style.display = 'none';
    if (formReg) formReg.style.display = 'block';
    if (title) title.innerText = '✨ Új Vállalkozási Fiók Regisztrációja';
    setTimeout(() => { document.getElementById('reg-company')?.focus(); }, 100);
  }
}

function fillDemoCreds(email, pwd) {
  const emailInput = document.getElementById('login-email');
  const pwdInput = document.getElementById('login-password');
  if (emailInput) emailInput.value = email;
  if (pwdInput) pwdInput.value = pwd;
  showToast(`Demo adatok betöltve: ${email}`, 'info', 1500);
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const btn = document.getElementById('btn-login-submit');

  btn.innerText = 'Bejelentkezés... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    btn.innerText = '🚀 Bejelentkezés';
    btn.disabled = false;

    if (res.ok && data.status === 'success') {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('hub_auth_token', authToken);
      closeModal('modal-auth');
      renderUserNavbar();
      showToast(data.message || 'Sikeres bejelentkezés!', 'success', 3500);
      loadModules();
      loadStats();
    } else {
      showToast(data.detail || 'Hibás bejelentkezési adatok!', 'error');
    }
  } catch (err) {
    btn.innerText = '🚀 Bejelentkezés';
    btn.disabled = false;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const company_name = document.getElementById('reg-company').value.trim();
  const full_name = document.getElementById('reg-fullname').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const phone = document.getElementById('reg-phone').value.trim();
  const password = document.getElementById('reg-password').value;
  const confirm = document.getElementById('reg-password-confirm').value;
  const btn = document.getElementById('btn-register-submit');

  if (password !== confirm) {
    showToast('A megadott jelszavak nem egyeznek!', 'warning');
    return;
  }

  btn.innerText = 'Regisztráció folyamatban... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name, company_name, phone })
    });

    const data = await res.json();
    btn.innerText = '✨ Fiók Létrehozása & Belépés';
    btn.disabled = false;

    if (res.ok && data.status === 'success') {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem('hub_auth_token', authToken);
      closeModal('modal-auth');
      renderUserNavbar();
      showToast(`Sikeres regisztráció! Üdvözlünk, ${currentUser.company_name}!`, 'success', 4000);
      loadModules();
      loadStats();
      setTimeout(() => {
        openIntegrationsModal();
        showToast('Most kösse be vállalkozása rendszereit (Gmail, GitHub stb.)!', 'info', 5000);
      }, 500);
    } else {
      showToast(data.detail || 'Hiba a regisztráció során!', 'error');
    }
  } catch (err) {
    btn.innerText = '✨ Fiók Létrehozása & Belépés';
    btn.disabled = false;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

async function logoutUser() {
  try {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      headers: getAuthHeaders(false)
    });
  } catch (_) {}

  authToken = null;
  currentUser = null;
  activeTenant = null;
  localStorage.removeItem('hub_auth_token');

  const banner = document.getElementById('active-tenant-banner');
  if (banner) banner.style.display = 'none';

  renderUserNavbar();
  loadModules();
  loadStats();
  showToast('Sikeresen kijelentkeztél.', 'info', 2500);
}

// --- Integrations Vault Presets & Management ---
const INTEGRATION_PRESETS = {
  gmail: {
    name: "Központi Google Workspace / Gmail Fiók",
    icon: "📧",
    desc: "Szükséges az automata bejövő email szortírozáshoz, árajánlatok és számlák közvetlen kézbesítéséhez.",
    fields: [
      { key: "email", label: "Email cím", type: "email", placeholder: "iroda@cegnev.hu", required: true },
      { key: "app_password", label: "Google Alkalmazás Jelszó (App Password)", type: "password", placeholder: "16 betűs jelszó (abcd efgh ijkl mnop)", required: true },
      { key: "imap_host", label: "IMAP Szerver", type: "text", default: "imap.gmail.com" },
      { key: "smtp_host", label: "SMTP Szerver", type: "text", default: "smtp.gmail.com" }
    ]
  },
  github: {
    name: "Céges GitHub Fiók / Repository",
    icon: "🐙",
    desc: "Szükséges a CI/CD, automata kódellenőrzés és release készítés modulokhoz.",
    fields: [
      { key: "username", label: "GitHub Felhasználónév / Szervezet", type: "text", placeholder: "cegnev-dev", required: true },
      { key: "token", label: "GitHub Personal Access Token (PAT)", type: "password", placeholder: "ghp_...", required: true },
      { key: "repo", label: "Repository (pl. szervezet/repo-nev)", type: "text", placeholder: "cegnev/fo-projekt", required: true }
    ]
  },
  szamlazz: {
    name: "Számlázz.hu Agent Kapcsolat",
    icon: "🧾",
    desc: "Szükséges az e-számlák, díjbekérők és sztornók 100%-ban automata kiállításához.",
    fields: [
      { key: "agent_key", label: "Számla Agent Kulcs", type: "password", placeholder: "szamlazz_agent_...", required: true }
    ]
  },
  billingo: {
    name: "Billingo API v3 Kapcsolat",
    icon: "💳",
    desc: "Billingo online számlázó rendszer integrációja e-számlákhoz és tömeges díjbekérőkhöz.",
    fields: [
      { key: "api_key", label: "Billingo API Kulcs (v3)", type: "password", placeholder: "billingo_api_...", required: true },
      { key: "block_id", label: "Számlatömb Azonosító (Block ID)", type: "text", placeholder: "123456" }
    ]
  },
  nav: {
    name: "NAV Online Számla Rendszer",
    icon: "🏛️",
    desc: "Szükséges a bejövő és kimenő számlák NAV adatszolgáltatásának ellenőrzéséhez és adategyeztetéshez.",
    fields: [
      { key: "tech_user", label: "Technikai Felhasználónév", type: "text", placeholder: "abcdef123456", required: true },
      { key: "tech_password", label: "Technikai Felhasználó Jelszava", type: "password", required: true },
      { key: "sign_key", label: "XML Aláírókulcs", type: "password", required: true },
      { key: "exchange_key", label: "XML Cserekulcs", type: "password", required: true }
    ]
  },
  meta: {
    name: "Meta / WhatsApp Business Cloud API",
    icon: "💬",
    desc: "Szükséges az automata WhatsApp és Messenger értesítésekhez, ügyfélszolgálati chatbothoz.",
    fields: [
      { key: "api_token", label: "Meta Graph API Hozzáférési Token", type: "password", placeholder: "EAA...", required: true },
      { key: "phone_id", label: "WhatsApp Phone Number ID", type: "text", placeholder: "10987654321", required: true },
      { key: "waba_id", label: "WhatsApp Business Account ID", type: "text", placeholder: "1234567890" }
    ]
  },
  webshop: {
    name: "Webáruház (WooCommerce / Shopify / Unas)",
    icon: "🛒",
    desc: "Szükséges az elhagyott kosarak, utánvét ellenőrzések, és készlet szinkronizáció modulokhoz.",
    fields: [
      { key: "store_url", label: "Webáruház Webcíme (Store URL)", type: "text", placeholder: "https://www.cegemboltja.hu", required: true },
      { key: "api_key", label: "Consumer Key / API Key", type: "password", placeholder: "ck_...", required: true },
      { key: "api_secret", label: "Consumer Secret / API Secret", type: "password", placeholder: "cs_...", required: true }
    ]
  },
  ai: {
    name: "AI Szolgáltató (OpenAI / Claude / Gemini API)",
    icon: "🤖",
    desc: "Saját céges API kvóta bekötése az AI munkafolyamatokhoz.",
    fields: [
      { key: "api_key", label: "AI API Kulcs", type: "password", placeholder: "sk-...", required: true },
      { key: "model", label: "Alapértelmezett Modell", type: "text", placeholder: "gpt-4o vagy claude-3-5-sonnet" }
    ]
  },
  custom: {
    name: "Egyedi Vállalati ERP / CRM / Webhook",
    icon: "🗄️",
    desc: "Bármilyen belső vállalatirányítási rendszer, adatbázis vagy webhook bekötése.",
    fields: [
      { key: "endpoint_url", label: "API / Webhook Végpont URL", type: "text", placeholder: "https://erp.ceg.hu/api", required: true },
      { key: "auth_token", label: "Bearer Token vagy Hitelesítő Fejléc", type: "password", placeholder: "Bearer ..." }
    ]
  }
};

async function openIntegrationsModal() {
  if (!currentUser) {
    openAuthModal('login');
    return;
  }
  const modal = document.getElementById('modal-integrations');
  if (modal) modal.style.display = 'flex';

  selectIntegrationPreset(selectedPresetKey || 'gmail');
  await loadUserIntegrations();
}

async function loadUserIntegrations() {
  const container = document.getElementById('vault-connected-list');
  const countEl = document.getElementById('vault-connected-count');
  if (!container) return;

  container.innerHTML = `<div class="loading-state">Bekötött szolgáltatások betöltése...</div>`;

  try {
    const res = await fetch('/api/v1/integrations', {
      headers: getAuthHeaders(false)
    });
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    const data = await res.json();
    const list = data.integrations || [];

    if (countEl) countEl.innerText = list.length;

    if (list.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 20px; background: rgba(255,255,255,0.02); border: 1px dashed var(--border); border-radius: var(--radius-md); text-align: center; color: var(--text-muted);">
          <p>Még nincs bekötött külső szolgáltatása. Válasszon az alábbi listából egy rendszert (pl. Google Workspace / Gmail vagy GitHub), és adja meg a hozzáférést a beállításhoz!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = list.map(item => {
      const preset = INTEGRATION_PRESETS[item.service_type] || { icon: '⚡' };
      const creds = item.credentials || {};
      const isOAuth = creds.auth_type === 'oauth2';

      let credRows = '';
      if (isOAuth) {
        credRows = `
          <div class="vault-card-field">
            <span class="vault-field-key">Hitelesítés:</span>
            <span class="vault-field-val" style="color: #60a5fa; font-weight: 600;">OAuth 2.0 Protokoll</span>
          </div>
          <div class="vault-card-field">
            <span class="vault-field-key">Fiók:</span>
            <span class="vault-field-val" style="color: #fff; font-weight: 600;" title="${escapeHtml(creds.account_email || '')}">${escapeHtml(creds.account_email || creds.account_name || 'Csatlakoztatva')}</span>
          </div>
          ${creds.scopes ? `
            <div class="vault-card-field">
              <span class="vault-field-key">Hatókörök:</span>
              <span class="vault-field-val" style="font-size: 10px;" title="${escapeHtml(creds.scopes)}">${escapeHtml(creds.scopes.slice(0, 30))}...</span>
            </div>
          ` : ''}
          ${creds.is_sandbox ? `
            <div class="vault-card-field">
              <span class="vault-field-key">Mód:</span>
              <span class="badge badge-needs_setup" style="font-size: 10px;">🧪 Sandbox Teszt</span>
            </div>
          ` : ''}
        `;
      } else {
        credRows = Object.entries(creds).map(([k, v]) => `
          <div class="vault-card-field">
            <span class="vault-field-key">${escapeHtml(k)}:</span>
            <span class="vault-field-val" title="${escapeHtml(String(v))}">${escapeHtml(String(v))}</span>
          </div>
        `).join('');
      }

      return `
        <div class="vault-card" style="${isOAuth ? 'border-color: rgba(59,130,246,0.3); background: #0c1527;' : ''}">
          <div>
            <div class="vault-card-header">
              <div class="vault-card-title">
                <span>${preset.icon}</span>
                <span>${escapeHtml(item.service_name)}</span>
              </div>
              <div style="display: flex; gap: 6px; align-items: center;">
                ${isOAuth ? '<span class="badge badge-oauth">🛡️ OAuth 2.0</span>' : ''}
                <span class="badge badge-active">🟢 Aktív</span>
              </div>
            </div>
            <div class="vault-card-body">
              ${credRows}
              ${item.notes ? `<div style="margin-top: 8px; font-size: 11px; color: var(--text-subtle);">📝 ${escapeHtml(item.notes)}</div>` : ''}
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px;">
            <button class="btn btn-outline btn-sm text-danger" onclick="deleteIntegration(${item.id})" style="border-color: rgba(239,68,68,0.3); font-size: 11px;">
              🗑️ Eltávolítás
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div class="text-danger" style="padding: 12px;">Hiba: ${escapeHtml(err.message)}</div>`;
  }
}

function selectIntegrationPreset(key) {
  selectedPresetKey = key;
  document.querySelectorAll('.vault-preset-chips .preset-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(key));
  });

  const preset = INTEGRATION_PRESETS[key];
  if (!preset) return;

  const typeInput = document.getElementById('int-service-type');
  if (typeInput) typeInput.value = key;

  const nameInput = document.getElementById('int-service-name');
  if (nameInput) nameInput.value = preset.name;

  renderDynamicPresetFields(preset);
}

function renderDynamicPresetFields(preset) {
  const container = document.getElementById('vault-dynamic-fields');
  if (!container) return;

  container.innerHTML = preset.fields.map(f => {
    let inputHtml = '';
    if (f.type === 'password') {
      inputHtml = `
        <div class="password-wrapper">
          <input type="password" name="cred_${f.key}" class="form-control" placeholder="${f.placeholder || ''}" ${f.required ? 'required' : ''}>
          <button type="button" class="btn-toggle-eye" onclick="togglePasswordVisibility(this)">👁️</button>
        </div>
      `;
    } else {
      inputHtml = `
        <input type="${f.type || 'text'}" name="cred_${f.key}" class="form-control" value="${f.default || ''}" placeholder="${f.placeholder || ''}" ${f.required ? 'required' : ''}>
      `;
    }

    return `
      <div class="form-group" style="margin-bottom: 0;">
        <label>${f.label} ${f.required ? '<span class="text-danger">*</span>' : ''}</label>
        ${inputHtml}
      </div>
    `;
  }).join('');
}

async function handleSaveIntegration(event) {
  event.preventDefault();
  const service_type = document.getElementById('int-service-type').value;
  const service_name = document.getElementById('int-service-name').value.trim();
  const notes = document.getElementById('int-notes').value.trim();
  const form = document.getElementById('form-save-integration');
  const btn = document.getElementById('btn-save-integration');

  const preset = INTEGRATION_PRESETS[service_type];
  if (!preset) return;

  const credentials = {};
  for (const f of preset.fields) {
    const el = form.elements[`cred_${f.key}`];
    if (el) {
      const val = el.value.trim();
      if (f.required && !val) {
        showToast(`Kérjük adja meg a(z) '${f.label}' mezőt!`, 'warning');
        el.focus();
        return;
      }
      credentials[f.key] = val;
    }
  }

  btn.innerText = 'Mentés a Vaultba... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch('/api/v1/integrations', {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify({
        service_type,
        service_name,
        credentials,
        notes
      })
    });

    const data = await res.json();
    btn.innerText = '💾 Hozzáférés Biztonságos Mentése a Vaultba';
    btn.disabled = false;

    if (res.ok && data.status === 'success') {
      showToast(`'${service_name}' sikeresen elmentve a Vaultba!`, 'success');
      form.reset();
      selectIntegrationPreset(service_type);
      await loadUserIntegrations();
    } else {
      showToast(data.detail || 'Hiba a mentés során!', 'error');
    }
  } catch (err) {
    btn.innerText = '💾 Hozzáférés Biztonságos Mentése a Vaultba';
    btn.disabled = false;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

async function deleteIntegration(id) {
  if (!confirm("Biztosan törölni szeretné ezt a bekötött szolgáltatást a Vaultból?")) return;

  try {
    const res = await fetch(`/api/v1/integrations/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(false)
    });
    if (res.ok) {
      showToast('Integráció sikeresen törölve.', 'info');
      await loadUserIntegrations();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Hiba a törléskor', 'error');
    }
  } catch (e) {
    showToast(`Hálózati hiba: ${e.message}`, 'error');
  }
}

// --- Super Admin Client Management Platform ---
async function openAdminClientsModal() {
  if (!currentUser || currentUser.role !== 'superadmin') {
    showToast('Ehhez a művelethez Szuper Admin jogosultság szükséges!', 'error');
    return;
  }
  const modal = document.getElementById('modal-admin-clients');
  if (modal) modal.style.display = 'flex';
  await loadAdminClients();
}

async function loadAdminClients() {
  const tbody = document.getElementById('admin-clients-tbody');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6" class="text-center">Megbízók és ügyfelek lekérése...</td></tr>`;

  try {
    const res = await fetch('/api/v1/admin/clients', {
      headers: getAuthHeaders(false)
    });
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    const data = await res.json();
    allAdminClients = data.clients || [];

    const navCnt = document.getElementById('nav-client-count');
    if (navCnt) navCnt.innerText = allAdminClients.length;

    renderAdminClientsTable(allAdminClients);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center">Hiba: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function renderAdminClientsTable(clients) {
  const tbody = document.getElementById('admin-clients-tbody');
  if (!tbody) return;

  if (clients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Még nincsenek regisztrált ügyfelek.</td></tr>`;
    return;
  }

  tbody.innerHTML = clients.map(c => {
    const isCurrentActiveTenant = activeTenant && activeTenant.id === c.id;
    const intCount = c.integration_count || 0;
    const intBadgeClass = intCount > 0 ? 'badge-active' : 'badge-needs_setup';

    return `
      <tr style="${isCurrentActiveTenant ? 'background: rgba(245, 158, 11, 0.08);' : ''}">
        <td><code>#${c.id}</code></td>
        <td>
          <strong>${escapeHtml(c.company_name)}</strong>
          ${isCurrentActiveTenant ? '<span class="tenant-badge" style="margin-left: 6px;">AKTÍV MÓD</span>' : ''}
        </td>
        <td>${escapeHtml(c.full_name)}</td>
        <td>
          <div><a href="mailto:${escapeHtml(c.email)}" style="color:#93c5fd; text-decoration: none;">✉️ ${escapeHtml(c.email)}</a></div>
          ${c.phone ? `<div style="font-size: 11.5px; color: var(--text-muted);">📞 ${escapeHtml(c.phone)}</div>` : ''}
        </td>
        <td>
          <span class="badge ${intBadgeClass}">
            ${intCount > 0 ? `🟢 ${intCount} db bekötve` : '⚪ 0 bekötve'}
          </span>
        </td>
        <td>
          <div class="client-actions-cell">
            <button class="btn btn-warning btn-sm" onclick="enterTenantMode(${c.id})" title="Belépés az ügyfél környezetébe a modulok konfigurálásához">
              ⚙ Munka vele
            </button>
            <button class="btn btn-outline btn-sm" onclick="openClientIntegrationsModal(${c.id})" title="Ügyfél bekötött API és jelszó adatainak megtekintése">
              🔑 Hozzáférések
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterAdminClients() {
  const input = document.getElementById('admin-client-search');
  const q = (input ? input.value : '').toLowerCase().trim();
  if (!q) {
    renderAdminClientsTable(allAdminClients);
    return;
  }
  const filtered = allAdminClients.filter(c => 
    (c.company_name && c.company_name.toLowerCase().includes(q)) ||
    (c.full_name && c.full_name.toLowerCase().includes(q)) ||
    (c.email && c.email.toLowerCase().includes(q))
  );
  renderAdminClientsTable(filtered);
}

function enterTenantMode(clientId) {
  const client = allAdminClients.find(c => c.id === clientId);
  if (!client) return;

  activeTenant = client;

  const banner = document.getElementById('active-tenant-banner');
  const bannerName = document.getElementById('tenant-banner-client-name');
  const bannerContact = document.getElementById('tenant-banner-contact');
  const bannerEmail = document.getElementById('tenant-banner-email');
  const bannerCount = document.getElementById('tenant-banner-int-count');

  if (bannerName) bannerName.innerText = client.company_name;
  if (bannerContact) bannerContact.innerText = client.full_name;
  if (bannerEmail) bannerEmail.innerText = client.email;
  if (bannerCount) bannerCount.innerText = client.integration_count || 0;

  if (banner) banner.style.display = 'block';

  closeModal('modal-admin-clients');
  closeModal('modal-admin-client-details');

  showToast(`👑 Szuper Admin mód aktív: Mostantól a(z) '${client.company_name}' ügyfél fiókját konfigurálod!`, 'warning', 4500);

  loadModules();
}

function exitTenantMode() {
  activeTenant = null;
  const banner = document.getElementById('active-tenant-banner');
  if (banner) banner.style.display = 'none';

  showToast('Visszatértél a globális Hub nézetbe.', 'info', 2500);
  loadModules();
}

async function openClientIntegrationsModal(clientId) {
  if (!currentUser || currentUser.role !== 'superadmin') return;

  const modal = document.getElementById('modal-admin-client-details');
  const title = document.getElementById('client-details-title');
  const subtitle = document.getElementById('client-details-subtitle');
  const body = document.getElementById('client-details-body');
  const activateBtn = document.getElementById('btn-activate-client-from-details');

  if (modal) modal.style.display = 'flex';
  if (body) body.innerHTML = `<div class="loading-state">Ügyfél hozzáféréseinek és API kulcsainak lekérése...</div>`;

  try {
    const res = await fetch(`/api/v1/admin/clients/${clientId}`, {
      headers: getAuthHeaders(false)
    });
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    const data = await res.json();
    const client = data.client;
    const integrations = data.integrations || [];

    if (title) title.innerText = `🔑 ${client.company_name} - Bekötött Rendszerek`;
    if (subtitle) subtitle.innerText = `${client.full_name} (${client.email}) | ${integrations.length} db bekötött szolgáltatás`;

    if (activateBtn) {
      activateBtn.onclick = () => enterTenantMode(client.id);
    }

    if (integrations.length === 0) {
      body.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--text-muted);">
          <p>Ez az ügyfél még nem adott meg hozzáférési adatokat a Vaultban.</p>
        </div>
      `;
      return;
    }

    body.innerHTML = integrations.map(item => {
      const preset = INTEGRATION_PRESETS[item.service_type] || { icon: '⚡' };
      const creds = item.credentials || {};
      const rows = Object.entries(creds).map(([k, v]) => `
        <div class="cred-item">
          <span class="cred-label">${escapeHtml(k)}:</span>
          <div class="cred-val-wrap">
            <span class="cred-val">${escapeHtml(String(v))}</span>
            <button class="btn-copy-sm" onclick="copyCredValue('${escapeHtml(String(v))}', this)">Másolás</button>
          </div>
        </div>
      `).join('');

      return `
        <div class="cred-box">
          <div class="cred-box-header">
            <div class="cred-box-title">
              <span>${preset.icon}</span>
              <span>${escapeHtml(item.service_name)}</span>
            </div>
            <span class="badge badge-active">${item.service_type.toUpperCase()}</span>
          </div>
          <div>
            ${rows}
            ${item.notes ? `<div style="margin-top: 8px; font-size: 11px; color: #cbd5e1;">📝 <em>${escapeHtml(item.notes)}</em></div>` : ''}
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    if (body) body.innerHTML = `<div class="text-danger" style="padding: 16px;">Hiba: ${escapeHtml(err.message)}</div>`;
  }
}

function copyCredValue(val, btn) {
  navigator.clipboard.writeText(val).then(() => {
    const orig = btn.innerText;
    btn.innerText = '✓ Másolva';
    setTimeout(() => { btn.innerText = orig; }, 1500);
  });
}

// ==========================================================================
// OAuth 2.0 Client & Admin Handlers
// ==========================================================================

function checkOAuthRedirectParams() {
  const params = new URLSearchParams(window.location.search);
  if (params.has('oauth_success')) {
    const provider = params.get('provider') || 'szolgáltató';
    const account = params.get('account') || '';
    const cleanUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);

    showToast(`✅ ${provider.toUpperCase()} fiók ${account ? '(' + decodeURIComponent(account) + ') ' : ''}sikeresen csatlakoztatva OAuth 2.0-val!`, 'success', 5000);
    setTimeout(() => {
      openIntegrationsModal();
    }, 600);
  } else if (params.has('oauth_error')) {
    const err = params.get('oauth_error');
    const provider = params.get('provider') || '';
    const cleanUrl = window.location.origin + window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
    showToast(`❌ OAuth hiba (${provider}): ${decodeURIComponent(err)}`, 'error', 5000);
  }
}

async function startOAuthFlow(provider) {
  if (!currentUser) {
    openAuthModal('login');
    showToast("Kérjük, először jelentkezzen be az OAuth összekapcsoláshoz!", 'warning');
    return;
  }

  showToast(`Átirányítás ${provider.toUpperCase()} OAuth 2.0 hitelesítéshez...`, 'info', 2000);

  try {
    const res = await fetch(`/api/v1/oauth/${provider}/authorize`, {
      headers: getAuthHeaders(false)
    });
    const data = await res.json();
    if (res.ok && data.auth_url) {
      window.location.href = data.auth_url;
    } else {
      showToast(data.detail || 'Nem sikerült elindítani az OAuth folyamatot.', 'error');
    }
  } catch (err) {
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

function switchAdminTab(tab) {
  const tabClientsBtn = document.getElementById('tab-admin-clients');
  const tabOAuthBtn = document.getElementById('tab-admin-oauth');
  const viewClients = document.getElementById('admin-view-clients');
  const viewOAuth = document.getElementById('admin-view-oauth');

  if (tab === 'clients') {
    if (tabClientsBtn) tabClientsBtn.classList.add('active');
    if (tabOAuthBtn) tabOAuthBtn.classList.remove('active');
    if (viewClients) viewClients.style.display = 'block';
    if (viewOAuth) viewOAuth.style.display = 'none';
  } else {
    if (tabClientsBtn) tabClientsBtn.classList.remove('active');
    if (tabOAuthBtn) tabOAuthBtn.classList.add('active');
    if (viewClients) viewClients.style.display = 'none';
    if (viewOAuth) viewOAuth.style.display = 'block';
    loadAdminOAuthApps();
  }
}

async function loadAdminOAuthApps() {
  const container = document.getElementById('admin-oauth-apps-grid');
  if (!container) return;
  container.innerHTML = `<div class="loading-state">OAuth alkalmazások betöltése...</div>`;

  try {
    const res = await fetch('/api/v1/admin/oauth-apps', {
      headers: getAuthHeaders(false)
    });
    if (!res.ok) throw new Error(`HTTP hiba: ${res.status}`);
    const data = await res.json();
    const apps = data.oauth_apps || [];

    container.innerHTML = apps.map(app => {
      return `
        <div class="oauth-app-card" id="oauth-card-${app.provider}">
          <div class="oauth-app-card-header">
            <div class="oauth-app-title">
              <span>${app.icon || '⚡'}</span>
              <span>${escapeHtml(app.name)}</span>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
              ${app.sandbox_mode ? '<span class="badge badge-needs_setup">🧪 Sandbox Mód</span>' : '<span class="badge badge-active">🟢 Éles Mód</span>'}
              <span class="badge badge-${app.is_enabled ? 'active' : 'disabled'}">${app.is_enabled ? 'Bekapcsolva' : 'Kikapcsolva'}</span>
            </div>
          </div>

          <!-- Redirect URI for Developer Console -->
          <div class="form-group" style="margin-bottom: 8px;">
            <label style="font-size: 11.5px;">Authorized Redirect URI (Másolja be a ${escapeHtml(app.name)} fejlesztői felületre):</label>
            <div class="redirect-uri-box">
              <span class="redirect-uri-text" id="red-uri-${app.provider}">${escapeHtml(app.suggested_redirect_uri)}</span>
              <button type="button" class="btn-copy-sm" onclick="copyRedirectUri('${escapeHtml(app.suggested_redirect_uri)}', this)">Másolás</button>
            </div>
            ${app.production_redirect_uri !== app.suggested_redirect_uri ? `
              <div style="font-size: 11px; color: var(--text-subtle); margin-top: -6px; margin-bottom: 10px;">
                Éles Vercel callback: <code>${escapeHtml(app.production_redirect_uri)}</code>
              </div>
            ` : ''}
          </div>

          <!-- Configuration Form -->
          <form onsubmit="saveAdminOAuthApp('${app.provider}', event)">
            <div class="form-row">
              <div class="form-group" style="flex: 1;">
                <label>Client ID (Alkalmazás azonosító)</label>
                <input type="text" name="client_id" class="form-control" value="${escapeHtml(app.client_id || '')}" placeholder="pl. 123456...apps.googleusercontent.com">
              </div>
              <div class="form-group" style="flex: 1;">
                <label>Client Secret (Titkos kulcs)</label>
                <div class="password-wrapper">
                  <input type="password" name="client_secret" class="form-control" value="${app.has_secret ? '******' : ''}" placeholder="${app.has_secret ? 'Kulcs elmentve (írjon be újat a cseréhez)' : 'Adja meg a secretet'}">
                  <button type="button" class="btn-toggle-eye" onclick="togglePasswordVisibility(this)">👁️</button>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label>Engedélyek (Scopes)</label>
              <input type="text" name="scopes" class="form-control" value="${escapeHtml(app.scopes || '')}" placeholder="Szóközzel vagy vesszővel elválasztva">
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px; flex-wrap: wrap; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 16px;">
                <label style="display: flex; align-items: center; gap: 8px; font-size: 12px; cursor: pointer;">
                  <input type="checkbox" name="sandbox_mode" ${app.sandbox_mode ? 'checked' : ''}>
                  <span>🧪 Sandbox / Teszt mód (azonnali kipróbálás felhő setup nélkül)</span>
                </label>
                <label style="display: flex; align-items: center; gap: 8px; font-size: 12px; cursor: pointer;">
                  <input type="checkbox" name="is_enabled" ${app.is_enabled ? 'checked' : ''}>
                  <span>Aktív</span>
                </label>
              </div>
              <button type="submit" class="btn btn-primary btn-sm">
                <span class="icon">💾</span> Mentés
              </button>
            </div>
          </form>
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div class="text-danger" style="padding: 16px;">Hiba: ${escapeHtml(err.message)}</div>`;
  }
}

async function saveAdminOAuthApp(provider, event) {
  event.preventDefault();
  const form = event.target;
  const client_id = form.elements['client_id'].value.trim();
  const client_secret = form.elements['client_secret'].value.trim();
  const scopes = form.elements['scopes'].value.trim();
  const sandbox_mode = form.elements['sandbox_mode'].checked;
  const is_enabled = form.elements['is_enabled'].checked;
  const btn = form.querySelector('button[type="submit"]');

  const origText = btn.innerHTML;
  btn.innerText = 'Mentés... ⏳';
  btn.disabled = true;

  try {
    const res = await fetch(`/api/v1/admin/oauth-apps/${provider}`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify({
        client_id,
        client_secret,
        scopes,
        sandbox_mode,
        is_enabled
      })
    });

    const data = await res.json();
    btn.innerHTML = origText;
    btn.disabled = false;

    if (res.ok && data.status === 'success') {
      showToast(data.message || 'OAuth beállítások sikeresen mentve!', 'success');
      loadAdminOAuthApps();
    } else {
      showToast(data.detail || 'Hiba a mentés során', 'error');
    }
  } catch (err) {
    btn.innerHTML = origText;
    btn.disabled = false;
    showToast(`Hálózati hiba: ${err.message}`, 'error');
  }
}

function copyRedirectUri(uri, btn) {
  navigator.clipboard.writeText(uri).then(() => {
    const orig = btn.innerText;
    btn.innerText = '✓ Másolva';
    btn.style.background = '#10b981';
    btn.style.borderColor = '#10b981';
    setTimeout(() => {
      btn.innerText = orig;
      btn.style.background = '';
      btn.style.borderColor = '';
    }, 1500);
  });
}