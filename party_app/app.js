/* 路見不秤 ➤ 拔雕相見：配對任務 App */
"use strict";

// ═══ 設定 ═══
const CONFIG = {
  // 貼上 Google Apps Script Web App 的網址即可啟用「解鎖狀態回報」；留空 = 純離線模式
  SYNC_URL: "",
  STORAGE_KEY: "party_state_v1",
};

const SALT = window.PARTY_SALT;
const PEOPLE = window.PARTY_PEOPLE;

// ═══ 狀態（localStorage 為唯一真實來源，換頁/斷線/重整都不會掉） ═══
let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) { /* 私密瀏覽等情況：退化為記憶體狀態 */ }
  return { me: null, wrong: 0, done: false, doneAt: null, reveal: null, queue: [] };
}
// 舊版狀態補上賓果欄位
state.bingo = state.bingo || { claims: {}, lines: 0, lineAt: null, fullAt: null };
function saveState() {
  try { localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
}

// ═══ 工具：正規化與雜湊（需與 tools/generate_data.py 一致） ═══
function norm(s) {
  return s.normalize("NFKC").toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
}
async function sha256Bytes(str) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
  return new Uint8Array(buf);
}
async function sha256Hex(str) {
  const b = await sha256Bytes(str);
  return [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
}
async function decryptPayload(b64, aliasNorm) {
  const data = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const out = new Uint8Array(data.length);
  const keyBase = SALT + aliasNorm + "|k";
  for (let off = 0, i = 0; off < data.length; off += 32, i++) {
    const block = await sha256Bytes(`${keyBase}:${i}`);
    for (let j = 0; j < 32 && off + j < data.length; j++) out[off + j] = data[off + j] ^ block[j];
  }
  return JSON.parse(new TextDecoder().decode(out));
}

// ═══ 解鎖狀態回報（離線佇列 + 重送，Apps Script 端以暱稱 upsert） ═══
let flushing = false;
function track(type) {
  if (!CONFIG.SYNC_URL) return;
  state.queue.push({
    type, name: state.me, wrong: state.wrong,
    done: state.done, doneAt: state.doneAt,
    lines: state.bingo.lines, ts: Date.now(),
  });
  saveState();
  flushQueue();
}
async function flushQueue() {
  if (flushing || !CONFIG.SYNC_URL || !navigator.onLine) return;
  flushing = true;
  try {
    while (state.queue.length) {
      // Content-Type 用 text/plain 避開 CORS preflight（Apps Script 不支援 OPTIONS）
      const res = await fetch(CONFIG.SYNC_URL, {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify(state.queue[0]),
      });
      if (!res.ok) break;          // 伺服器異常：留在佇列，之後再送
      state.queue.shift();
      saveState();
    }
  } catch (e) { /* 斷線：佇列保留，等 online 事件或下次動作重送 */ }
  flushing = false;
}
window.addEventListener("online", flushQueue);
setInterval(flushQueue, 30_000);

// ═══ 畫面切換 ═══
const $ = (sel) => document.querySelector(sel);
const screens = ["login", "card", "quest", "done", "bingo"];
function show(name) {
  screens.forEach((s) => $("#screen-" + s).classList.toggle("hidden", s !== name));
  $("#tabbar").classList.toggle("hidden", name === "login");
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.nav === name || (t.dataset.nav === "quest" && name === "done")));
  window.scrollTo(0, 0);
}
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    if (t.dataset.nav === "quest") return state.done ? renderDone() : show("quest");
    if (t.dataset.nav === "bingo") renderBingo();
    show(t.dataset.nav);
  }));

function me() { return PEOPLE.find((p) => p.name === state.me); }

// ═══ 登入頁 ═══
function initLogin() {
  const sel = $("#who");
  PEOPLE.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.name; o.textContent = p.name;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => { $("#btn-login").disabled = !sel.value; });
  $("#btn-login").addEventListener("click", () => {
    if (!sel.value) return;
    state.me = sel.value;
    saveState();
    track("login");
    enter();
  });
  $("#btn-logout").addEventListener("click", () => {
    if (!confirm("換人登入會清除這支手機上的進度，確定？")) return;
    state = { me: null, wrong: 0, done: false, doneAt: null, reveal: null, queue: [],
      bingo: { claims: {}, lines: 0, lineAt: null, fullAt: null } };
    saveState();
    sel.value = "";
    $("#btn-login").disabled = true;
    show("login");
  });
}

// ═══ 名片頁 ═══
const ZODIAC = [["摩羯", 120], ["水瓶", 219], ["雙魚", 321], ["牡羊", 420], ["金牛", 521], ["雙子", 621],
  ["巨蟹", 723], ["獅子", 823], ["處女", 923], ["天秤", 1023], ["天蠍", 1122], ["射手", 1222], ["摩羯", 1232]];
function zodiacOf(birthday) {
  const m = birthday.match(/(\d+)\/(\d+)$/);
  if (!m) return "";
  const md = +m[1] * 100 + +m[2];
  return (ZODIAC.find(([, until]) => md < until) || ZODIAC[0])[0] + "座";
}
function renderCard() {
  const p = me();
  $("#card-name").textContent = p.name;
  const z = zodiacOf(p.birthday);
  $("#card-meta").textContent = `🎂 ${p.birthday}${z ? " · " + z : ""}`;
  const url = "https://www.instagram.com/" + p.ig;
  const link = $("#card-ig");
  link.href = url; link.textContent = "@" + p.ig;
  const qr = qrcode(0, "M");
  qr.addData(url);
  qr.make();
  $("#card-qr").innerHTML = qr.createSvgTag({ cellSize: 5, margin: 3, scalable: true });
  const chip = $("#card-status");
  chip.textContent = state.done ? "✅ 配對任務已完成" : "🧩 配對任務進行中";
  chip.classList.toggle("ok", state.done);
}

// ═══ 猜謎頁 ═══
function initQuest() {
  $("#quest-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const input = $("#guess");
    const guess = input.value.trim();
    const p = me();
    if (!guess || !p || !p.quest || state.done) return;
    const a = norm(guess);
    const quest = p.quest;
    const hit = a && (await matchAnswer(quest, a));
    if (hit) {
      state.done = true;
      state.doneAt = Date.now();
      state.reveal = hit;
      saveState();
      track("unlock");
      renderCard();
      renderDone();
      return;
    }
    state.wrong += 1;
    saveState();
    track("wrong");
    $("#wrong-count").textContent = state.wrong;
    const known = PEOPLE.some((p) => norm(p.name) === a);
    setMsg(known ? "有這位朋友，但不是你要找的人 😜" : "名單上沒有這個暱稱，檢查一下錯字？", "err");
    const panel = $("#screen-quest .panel");
    panel.classList.remove("shake");
    requestAnimationFrame(() => panel.classList.add("shake"));
    input.select();
  });
}
async function matchAnswer(quest, aliasNorm) {
  const h = await sha256Hex(SALT + aliasNorm);
  const entry = quest.answers.find((x) => x.h === h);
  if (!entry) return null;
  try { return await decryptPayload(entry.p, aliasNorm); } catch (e) { return null; }
}
function setMsg(text, cls) {
  const el = $("#quest-msg");
  el.textContent = text;
  el.className = "quest-msg " + (cls || "");
}
function renderQuest() {
  const p = me();
  if (!p.quest) {   // 主辦人沒有配對任務
    $("#quest-hint").textContent = "你是主辦人！你的任務是把大家灌醉，然後記得自己也要玩得開心 🍻";
    $("#quest-form").classList.add("hidden");
    $("#screen-quest .quest-foot").classList.add("hidden");
    setMsg("");
    return;
  }
  $("#quest-hint").textContent = p.quest.hint;
  $("#wrong-count").textContent = state.wrong;
  setMsg("答對才會解鎖對方的 IG ✨", "info");
}
function renderDatalist() {
  const dl = $("#names-dl");
  dl.innerHTML = "";
  PEOPLE.filter((q) => q.name !== state.me).forEach((q) => {
    const o = document.createElement("option");
    o.value = q.name;
    dl.appendChild(o);
  });
}

// ═══ 完成頁 ═══
function renderDone() {
  const r = state.reveal;
  $("#done-target").textContent = r.n;
  const link = $("#done-ig");
  link.href = "https://www.instagram.com/" + r.ig;
  link.textContent = "追蹤 @" + r.ig + " 📸";
  $("#done-me").textContent = state.me;
  $("#done-wrong").textContent = state.wrong + " 次";
  $("#done-time").textContent = new Date(state.doneAt).toLocaleString("zh-TW", {
    month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
  const box = $("#screen-done .confetti");
  if (!box.childElementCount) {
    const colors = ["#3ee6d8", "#ff8a5c", "#ffd166", "#f4602f", "#ffffff"];
    for (let i = 0; i < 60; i++) {
      const c = document.createElement("i");
      c.style.left = Math.random() * 100 + "%";
      c.style.background = colors[i % colors.length];
      c.style.animationDuration = 2.5 + Math.random() * 3 + "s";
      c.style.animationDelay = Math.random() * 2 + "s";
      box.appendChild(c);
    }
  }
  show("done");
}

// ═══ 人類賓果 ═══
// 每人依暱稱產生固定的 3×3 卡片：中央是主辦格，其餘 4 格系統驗證 + 4 格真人按確認。
// 同一個人只能填一格 → 連線至少認識 3 人、全滿要認識 9 人。
const HOST = "小柯";
const LINES = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];

function monthOf(p) { return +p.birthday.split("/")[1]; }
function seededRng(str) {                 // xmur3 + mulberry32
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  let a = (h ^= h >>> 16) >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function shuffled(arr, rng) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const HONOR_POOL = [
  { key: "h-drink",  text: "🍸 會調酒的人" },
  { key: "h-guitar", text: "🎸 會彈吉他的人" },
  { key: "h-driver", text: "🚗 今天開車載人來的司機" },
  { key: "h-sober",  text: "🚱 今天完全不喝酒的人" },
  { key: "h-nobeef", text: "🥩 不吃牛的人" },
  { key: "h-shrimp", text: "🦐 不吃蝦或對蝦過敏的人" },
  { key: "h-new",    text: "🌱 今天第一次見面的新朋友（聊滿 3 分鐘）" },
  { key: "h-sing",   text: "🎤 敢當場唱一句歌的人（要真的唱！）" },
  { key: "h-tarot",  text: "🔮 會塔羅或占卜的人" },
  { key: "h-mahj",   text: "🀄 會打麻將的人" },
  { key: "h-abroad", text: "✈️ 今年出過國的人" },
  { key: "h-phone",  text: "📱 手機跟你同款的人" },
  { key: "h-mbti",   text: "🧠 MBTI 跟你一樣的人" },
  { key: "h-gym",    text: "💪 一週健身三次以上的人" },
  { key: "h-dog",    text: "🐕 家裡有養狗的人" },
  { key: "h-swim",   text: "🏊 今天已經下過水的人" },
];

function autoPool(player) {
  const others = PEOPLE.filter((p) => p.name !== player.name);
  const pool = [];
  const byMonth = {};
  others.forEach((p) => { (byMonth[monthOf(p)] = byMonth[monthOf(p)] || []).push(p); });
  Object.entries(byMonth).forEach(([m, list]) => {
    if (list.length >= 3) pool.push({
      key: "a-m" + m, text: `🎂 ${m} 月壽星`,
      check: (p) => monthOf(p) === +m,
    });
  });
  const byZodiac = {};
  others.forEach((p) => {
    const z = zodiacOf(p.birthday);
    (byZodiac[z] = byZodiac[z] || []).push(p);
  });
  Object.entries(byZodiac).forEach(([z, list]) => {
    if (list.length >= 3) pool.push({
      key: "a-z" + z, text: `✨ ${z}的人`,
      check: (p) => zodiacOf(p.birthday) === z,
    });
  });
  const myZ = zodiacOf(player.birthday);
  if ((byZodiac[myZ] || []).length >= 2) pool.push({
    key: "a-samez", text: `🪞 跟你同星座（${myZ}）的人`,
    check: (p) => zodiacOf(p.birthday) === myZ,
  });
  const myM = monthOf(player);
  if ((byMonth[myM] || []).length >= 2) pool.push({
    key: "a-samem", text: `🎈 跟你同月生日的人`,
    check: (p) => monthOf(p) === myM,
  });
  if (others.some((p) => p.name.length === 1)) pool.push({
    key: "a-1char", text: "🈶 暱稱只有一個字的人",
    check: (p) => p.name.length === 1,
  });
  return pool;
}

function buildCard(player) {
  const rng = seededRng("bingo|" + player.name);
  const kindOf = (c) => c.key.match(/^a-(m|z)/)?.[0] || c.key;
  const picked = [];
  const kindCount = {};
  for (const c of shuffled(autoPool(player), rng)) {   // 同類條件（月份/星座）最多 2 格
    const k = kindOf(c);
    if ((kindCount[k] || 0) >= 2) continue;
    kindCount[k] = (kindCount[k] || 0) + 1;
    picked.push(c);
    if (picked.length === 4) break;
  }
  const autos = picked.map((c) => ({ ...c, type: "auto" }));
  const honors = shuffled(HONOR_POOL, rng).slice(0, 4)
    .map((c) => ({ ...c, type: "honor" }));
  const cells = shuffled([...autos, ...honors], rng);
  const center = player.name === HOST
    ? { key: "h-host", text: "🍻 跟一位還沒說過話的人乾一杯", type: "honor" }
    : { key: "h-host", text: `🍻 跟主辦 ${HOST} 乾一杯`, type: "honor", fixed: HOST };
  cells.splice(4, 0, center);
  return cells;
}

let bingoCard = null;
function renderBingo() {
  const p = me();
  if (!p) return;
  bingoCard = bingoCard || buildCard(p);
  const grid = $("#bingo-grid");
  grid.innerHTML = "";
  bingoCard.forEach((cell, i) => {
    const el = document.createElement("button");
    el.className = "bingo-cell" + (state.bingo.claims[i] ? " claimed" : "");
    el.innerHTML = `<span class="bc-text"></span><span class="bc-who"></span>`;
    el.querySelector(".bc-text").textContent = cell.text;
    el.querySelector(".bc-who").textContent = state.bingo.claims[i] || "";
    el.addEventListener("click", () => openCell(i));
    grid.appendChild(el);
  });
  $("#bingo-lines").textContent = state.bingo.lines + " 條線";
  $("#bingo-lines").classList.toggle("hot", state.bingo.lines > 0);
}

let modalIdx = null;
function openCell(i) {
  modalIdx = i;
  const cell = bingoCard[i];
  $("#bm-cond").textContent = cell.text;
  $("#bm-msg").textContent = "";
  $("#bm-msg").className = "quest-msg";
  const claimed = state.bingo.claims[i];
  $("#bm-step-input").classList.toggle("hidden", !!claimed);
  $("#bm-step-confirm").classList.add("hidden");
  $("#bm-remove").classList.toggle("hidden", !claimed);
  if (claimed) setBmMsg(`已由「${claimed}」達成 ✅`, "info");
  else $("#bm-name").value = cell.fixed || "";
  $("#bingo-modal").classList.remove("hidden");
}
function setBmMsg(t, cls) {
  const el = $("#bm-msg");
  el.textContent = t;
  el.className = "quest-msg " + (cls || "");
}
function findPerson(input) {
  const a = norm(input);
  return a && PEOPLE.find((p) => norm(p.name) === a);
}
$("#bm-close").addEventListener("click", () => $("#bingo-modal").classList.add("hidden"));
$("#bingo-modal").addEventListener("click", (e) => {
  if (e.target.id === "bingo-modal") $("#bingo-modal").classList.add("hidden");
});
$("#bm-next").addEventListener("click", () => {
  const cell = bingoCard[modalIdx];
  const person = findPerson($("#bm-name").value);
  if (!person) return setBmMsg("名單上沒有這個暱稱 🤔", "err");
  if (person.name === state.me) return setBmMsg("不能填自己啦 😂", "err");
  if (cell.fixed && person.name !== cell.fixed) return setBmMsg(`這格只能找 ${cell.fixed} 喔`, "err");
  if (!cell.fixed && person.name === HOST && state.me !== HOST)
    return setBmMsg(`${HOST} 保留給中央那格 🍻，這格找別人吧`, "err");
  const used = Object.entries(state.bingo.claims).find(([j, n]) => +j !== modalIdx && n === person.name);
  if (used) return setBmMsg(`「${person.name}」已經用在別格了，同一人只能用一格！`, "err");
  if (cell.type === "auto") {
    if (!cell.check(person)) return setBmMsg(`「${person.name}」不符合這個條件，再問問別人 🔍`, "err");
    return claimCell(person.name);
  }
  // 真人確認
  $("#bm-step-input").classList.add("hidden");
  $("#bm-step-confirm").classList.remove("hidden");
  $("#bm-confirm").textContent = `我是 ${person.name} 本人，屬實 ✋`;
  $("#bm-confirm").dataset.name = person.name;
  setBmMsg("");
});
$("#bm-confirm").addEventListener("click", () => {
  claimCell($("#bm-confirm").dataset.name);
});
$("#bm-remove").addEventListener("click", () => {
  delete state.bingo.claims[modalIdx];
  state.bingo.lines = countLines();
  saveState();
  renderBingo();
  $("#bingo-modal").classList.add("hidden");
});
function countLines() {
  return LINES.filter((l) => l.every((i) => state.bingo.claims[i])).length;
}
function claimCell(name) {
  state.bingo.claims[modalIdx] = name;
  const before = state.bingo.lines;
  state.bingo.lines = countLines();
  const full = Object.keys(state.bingo.claims).length === 9;
  if (state.bingo.lines > before) {
    state.bingo.lineAt = Date.now();
    track("bingo_line");
  }
  if (full && !state.bingo.fullAt) {
    state.bingo.fullAt = Date.now();
    track("bingo_full");
  }
  saveState();
  renderBingo();
  $("#bingo-modal").classList.add("hidden");
  if (full) celebrateBingo("🏆 九宮格全滿！", "你已經認識了 9 位朋友，去跟主辦領大獎！");
  else if (state.bingo.lines > before) celebrateBingo("🎉 BINGO！", `第 ${state.bingo.lines} 條線達成，去跟主辦領獎～`);
}
function celebrateBingo(title, sub) {
  const el = document.createElement("div");
  el.className = "bingo-toast";
  el.innerHTML = `<b></b><span></span>`;
  el.querySelector("b").textContent = title;
  el.querySelector("span").textContent = sub;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

// ═══ 啟動 ═══
function enter() {
  bingoCard = null;
  renderCard();
  renderQuest();
  renderDatalist();
  show("card");
  flushQueue();
}
initLogin();
initQuest();
if (state.me && me()) enter();
else show("login");

// 離線快取（HTTPS / localhost 才會生效）
if ("serviceWorker" in navigator &&
    (location.protocol === "https:" || ["localhost", "127.0.0.1"].includes(location.hostname))) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
