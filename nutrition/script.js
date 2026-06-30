// ---------- Storage helpers ----------
const STORE_KEYS = {
  foods: 'nutri_foods',
  inbody: 'nutri_inbody',
  goal: 'nutri_protein_goal',
  apiKey: 'nutri_api_key',
};

function loadJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}
function saveJSON(key, val) {
  localStorage.setItem(key, JSON.stringify(val));
}

function todayStr() {
  const d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

let state = {
  foods: loadJSON(STORE_KEYS.foods, []), // {id, date, name, protein, calories, carbs, fat, note, createdAt}
  inbody: loadJSON(STORE_KEYS.inbody, []), // {id, date, weight, muscle, fat, fatmass, protein}
  goal: loadJSON(STORE_KEYS.goal, 120),
  apiKey: localStorage.getItem(STORE_KEYS.apiKey) || '',
};

// ---------- Tabs ----------
document.getElementById('tabs').addEventListener('click', (e) => {
  const btn = e.target.closest('.tab-btn');
  if (!btn) return;
  document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
  document.querySelectorAll('.day-content').forEach((s) => s.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(btn.dataset.target).classList.add('active');
  if (btn.dataset.target === 'page-history') renderHistory();
});

document.getElementById('todayLabel').textContent = `今日 ${todayStr()} · 每日蛋白質追蹤`;

// ---------- Protein ring / stats ----------
const RING_CIRC = 2 * Math.PI * 52;

function renderToday() {
  const today = todayStr();
  const todays = state.foods.filter((f) => f.date === today);
  const consumed = todays.reduce((s, f) => s + (Number(f.protein) || 0), 0);
  const calories = todays.reduce((s, f) => s + (Number(f.calories) || 0), 0);
  const goal = Number(state.goal) || 1;

  document.getElementById('proteinConsumed').textContent = Math.round(consumed);
  document.getElementById('proteinConsumed2').textContent = `${consumed.toFixed(1)} g`;
  document.getElementById('proteinGoal').textContent = goal;
  document.getElementById('proteinRemain').textContent = `${Math.max(0, goal - consumed).toFixed(1)} g`;
  document.getElementById('caloriesTotal').textContent = `${Math.round(calories)} kcal`;

  const ratio = Math.min(1, consumed / goal);
  const ring = document.getElementById('proteinRing');
  ring.style.strokeDasharray = RING_CIRC;
  ring.style.strokeDashoffset = RING_CIRC * (1 - ratio);
  ring.style.stroke = consumed >= goal ? 'var(--accent2)' : 'var(--accent)';

  const list = document.getElementById('todayList');
  if (todays.length === 0) {
    list.innerHTML = '<div class="empty-hint">今天還沒有紀錄，拍張照開始吧！</div>';
    return;
  }
  list.innerHTML = todays
    .slice()
    .reverse()
    .map(
      (f) => `
    <div class="food-item">
      <div class="food-item-main">
        <span class="food-item-name">${escapeHtml(f.name)}</span>
        <span class="food-item-sub">${f.note ? escapeHtml(f.note) + ' · ' : ''}${f.calories || 0} kcal</span>
      </div>
      <div class="food-item-right">
        <span class="food-item-protein">${f.protein}g</span>
        <button class="del-btn" data-id="${f.id}" title="刪除"><i class="ph-fill ph-x-circle"></i></button>
      </div>
    </div>`
    )
    .join('');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

document.getElementById('todayList').addEventListener('click', (e) => {
  const btn = e.target.closest('.del-btn');
  if (!btn) return;
  state.foods = state.foods.filter((f) => f.id !== btn.dataset.id);
  saveJSON(STORE_KEYS.foods, state.foods);
  renderToday();
});

// ---------- History ----------
function renderHistory() {
  const list = document.getElementById('historyList');
  const today = todayStr();
  const grouped = {};
  state.foods
    .filter((f) => f.date !== today)
    .forEach((f) => {
      grouped[f.date] = grouped[f.date] || [];
      grouped[f.date].push(f);
    });
  const dates = Object.keys(grouped).sort().reverse();
  if (dates.length === 0) {
    list.innerHTML = '<div class="empty-hint">尚無歷史紀錄</div>';
    return;
  }
  list.innerHTML = dates
    .map((d) => {
      const items = grouped[d];
      const totalProtein = items.reduce((s, f) => s + (Number(f.protein) || 0), 0);
      return `<div class="history-day-header">${d} · 共 ${totalProtein.toFixed(1)}g 蛋白質</div>` +
        items
          .map(
            (f) => `
        <div class="food-item">
          <div class="food-item-main">
            <span class="food-item-name">${escapeHtml(f.name)}</span>
            <span class="food-item-sub">${f.note ? escapeHtml(f.note) + ' · ' : ''}${f.calories || 0} kcal</span>
          </div>
          <div class="food-item-right">
            <span class="food-item-protein">${f.protein}g</span>
          </div>
        </div>`
          )
          .join('');
    })
    .join('');
}

// ---------- Add food: photo + AI ----------
let currentMode = 'food';
let currentPhotoBase64 = null;
let currentPhotoMediaType = null;

document.querySelectorAll('.mode-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-btn').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
  });
});

document.getElementById('pickPhotoBtn').addEventListener('click', () => {
  document.getElementById('photoInput').click();
});

document.getElementById('photoInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  currentPhotoMediaType = file.type || 'image/jpeg';
  const reader = new FileReader();
  reader.onload = () => {
    const dataUrl = reader.result;
    currentPhotoBase64 = dataUrl.split(',')[1];
    document.getElementById('photoPreview').src = dataUrl;
    document.getElementById('photoPreviewWrap').style.display = 'block';
    document.getElementById('analyzeStatus').textContent = '';
    document.getElementById('analyzeStatus').className = 'analyze-status';
    document.getElementById('foodForm').style.display = 'none';
  };
  reader.readAsDataURL(file);
});

document.getElementById('analyzeBtn').addEventListener('click', async () => {
  const statusEl = document.getElementById('analyzeStatus');
  if (!state.apiKey) {
    statusEl.textContent = '請先到「設定」頁輸入你的 Anthropic API 金鑰。';
    statusEl.className = 'analyze-status error';
    return;
  }
  statusEl.textContent = 'AI 分析中...';
  statusEl.className = 'analyze-status';
  document.getElementById('analyzeBtn').disabled = true;

  try {
    const result = await analyzeImageWithClaude(currentPhotoBase64, currentPhotoMediaType, currentMode);
    fillFormFromResult(result);
    statusEl.textContent = '辨識完成，請確認/修改後加入紀錄。';
    statusEl.className = 'analyze-status ok';
    document.getElementById('foodForm').style.display = 'flex';
  } catch (err) {
    statusEl.textContent = '分析失敗：' + err.message;
    statusEl.className = 'analyze-status error';
  } finally {
    document.getElementById('analyzeBtn').disabled = false;
  }
});

function fillFormFromResult(r) {
  document.getElementById('f_name').value = r.name || '';
  document.getElementById('f_protein').value = r.protein_g ?? '';
  document.getElementById('f_calories').value = r.calories_kcal ?? '';
  document.getElementById('f_carbs').value = r.carbs_g ?? '';
  document.getElementById('f_fat').value = r.fat_g ?? '';
  document.getElementById('f_note').value = r.serving || '';
}

async function analyzeImageWithClaude(base64, mediaType, mode) {
  const prompt =
    mode === 'food'
      ? '這是一張食物照片。請估算這份食物的營養成分（以你能辨識的整份/常見份量為準）。只回傳 JSON，不要任何其他文字，格式如下：{"name":"食物名稱","serving":"估計份量描述","protein_g":數字,"calories_kcal":數字,"carbs_g":數字,"fat_g":數字}'
      : '這是一張食品包裝上的營養標示照片。請讀取標示上的數值（若標示是「每100g」，請換算成包裝內單一份量或整包，並在 serving 註明你採用的份量）。只回傳 JSON，不要任何其他文字，格式如下：{"name":"產品名稱","serving":"份量描述","protein_g":數字,"calories_kcal":數字,"carbs_g":數字,"fat_g":數字}';

  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': state.apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-5',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type: mediaType, data: base64 } },
            { type: 'text', text: prompt },
          ],
        },
      ],
    }),
  });

  if (!resp.ok) {
    const errBody = await resp.json().catch(() => ({}));
    throw new Error(errBody?.error?.message || `HTTP ${resp.status}`);
  }
  const data = await resp.json();
  const text = (data.content || []).map((c) => c.text || '').join('');
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('AI 回應格式無法解析');
  return JSON.parse(jsonMatch[0]);
}

document.getElementById('foodForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const item = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
    date: todayStr(),
    name: document.getElementById('f_name').value.trim(),
    protein: parseFloat(document.getElementById('f_protein').value) || 0,
    calories: parseFloat(document.getElementById('f_calories').value) || 0,
    carbs: parseFloat(document.getElementById('f_carbs').value) || 0,
    fat: parseFloat(document.getElementById('f_fat').value) || 0,
    note: document.getElementById('f_note').value.trim(),
    createdAt: Date.now(),
  };
  state.foods.push(item);
  saveJSON(STORE_KEYS.foods, state.foods);

  e.target.reset();
  e.target.style.display = 'none';
  document.getElementById('photoPreviewWrap').style.display = 'none';
  document.getElementById('analyzeStatus').textContent = '';
  document.getElementById('photoInput').value = '';
  currentPhotoBase64 = null;

  renderToday();
});

// ---------- InBody ----------
document.getElementById('ib_date').value = todayStr();

function renderInbody() {
  const list = document.getElementById('inbodyList');
  if (state.inbody.length === 0) {
    list.innerHTML = '<div class="empty-hint">尚無 InBody 紀錄</div>';
    return;
  }
  list.innerHTML = state.inbody
    .slice()
    .sort((a, b) => b.date.localeCompare(a.date))
    .map(
      (r) => `
    <div class="food-item">
      <div class="food-item-main">
        <span class="food-item-name">${r.date}</span>
        <span class="food-item-sub">體重 ${r.weight ?? '-'}kg · 肌肉量 ${r.muscle ?? '-'}kg · 體脂率 ${r.fat ?? '-'}%</span>
      </div>
      <div class="food-item-right">
        <span class="food-item-protein">${r.protein ? r.protein + 'g' : ''}</span>
        <button class="del-btn" data-id="${r.id}" title="刪除"><i class="ph-fill ph-x-circle"></i></button>
      </div>
    </div>`
    )
    .join('');
}

document.getElementById('inbodyForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const item = {
    id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
    date: document.getElementById('ib_date').value || todayStr(),
    weight: parseFloat(document.getElementById('ib_weight').value) || null,
    muscle: parseFloat(document.getElementById('ib_muscle').value) || null,
    fat: parseFloat(document.getElementById('ib_fat').value) || null,
    fatmass: parseFloat(document.getElementById('ib_fatmass').value) || null,
    protein: parseFloat(document.getElementById('ib_protein').value) || null,
  };
  state.inbody.push(item);
  saveJSON(STORE_KEYS.inbody, state.inbody);

  if (item.protein) {
    state.goal = item.protein;
    saveJSON(STORE_KEYS.goal, state.goal);
    document.getElementById('s_proteinGoal').value = state.goal;
    renderToday();
  }

  e.target.reset();
  document.getElementById('ib_date').value = todayStr();
  renderInbody();
});

document.getElementById('inbodyList').addEventListener('click', (e) => {
  const btn = e.target.closest('.del-btn');
  if (!btn) return;
  state.inbody = state.inbody.filter((r) => r.id !== btn.dataset.id);
  saveJSON(STORE_KEYS.inbody, state.inbody);
  renderInbody();
});

// ---------- Settings ----------
document.getElementById('s_proteinGoal').value = state.goal;
document.getElementById('s_apiKey').value = '';
updateKeyStatus();

document.getElementById('saveGoalBtn').addEventListener('click', () => {
  const v = parseFloat(document.getElementById('s_proteinGoal').value);
  if (v > 0) {
    state.goal = v;
    saveJSON(STORE_KEYS.goal, state.goal);
    renderToday();
  }
});

document.getElementById('saveKeyBtn').addEventListener('click', () => {
  const v = document.getElementById('s_apiKey').value.trim();
  if (v) {
    state.apiKey = v;
    localStorage.setItem(STORE_KEYS.apiKey, v);
    document.getElementById('s_apiKey').value = '';
    updateKeyStatus();
  }
});

function updateKeyStatus() {
  const el = document.getElementById('keyStatus');
  el.textContent = state.apiKey ? '✅ 已儲存金鑰（僅存於本機）' : '尚未設定金鑰';
}

document.getElementById('clearAllBtn').addEventListener('click', () => {
  if (!confirm('確定要清除所有飲食與 InBody 紀錄嗎？此動作無法復原。')) return;
  localStorage.removeItem(STORE_KEYS.foods);
  localStorage.removeItem(STORE_KEYS.inbody);
  state.foods = [];
  state.inbody = [];
  renderToday();
  renderInbody();
  renderHistory();
});

// ---------- Init ----------
renderToday();
renderInbody();
