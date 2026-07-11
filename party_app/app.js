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
    done: state.done, doneAt: state.doneAt, ts: Date.now(),
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
const screens = ["login", "card", "quest", "done"];
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
    state = { me: null, wrong: 0, done: false, doneAt: null, reveal: null, queue: [] };
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
  const dl = $("#names-dl");
  dl.innerHTML = "";
  PEOPLE.filter((q) => q.name !== p.name).forEach((q) => {
    const o = document.createElement("option");
    o.value = q.name;
    dl.appendChild(o);
  });
  setMsg("答對才會解鎖對方的 IG ✨", "info");
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

// ═══ 啟動 ═══
function enter() {
  renderCard();
  renderQuest();
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
