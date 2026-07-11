/**
 * 解鎖狀態回報端點（Google Apps Script）
 *
 * 部署步驟：
 * 1. 開一份新的 Google 試算表（例如叫「配對任務狀態」）。
 * 2. 擴充功能 > Apps Script，把本檔全部貼上。
 * 3. 部署 > 新增部署作業 > 類型「網頁應用程式」：
 *    - 執行身分：我
 *    - 具有存取權的使用者：任何人
 * 4. 複製產生的網址，貼到 app.js 的 CONFIG.SYNC_URL。
 *
 * 每位參與者一列，依暱稱 upsert；試算表本身就是主辦即時儀表板。
 */
const SHEET_NAME = "狀態";
const HEADERS = ["暱稱", "已解鎖", "錯誤次數", "解鎖時間", "賓果線數", "名片冊", "最後更新", "最後事件"];

/** 排行榜資料（App 的「排行」分頁用 GET 讀取） */
function doGet() {
  const sheet = getSheet();
  const last = sheet.getLastRow();
  const rows = last > 1 ? sheet.getRange(2, 1, last - 1, HEADERS.length).getValues() : [];
  const data = rows.map(function (r) {
    return {
      name: r[0],
      done: r[1] === "✅",
      wrong: Number(r[2]) || 0,
      doneAt: r[3] ? new Date(r[3]).getTime() : null,
      lines: Number(r[4]) || 0,
      meets: Number(r[5]) || 0,
    };
  });
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000); // 53 人同時操作時避免互相蓋寫
  try {
    const d = JSON.parse(e.postData.contents);
    if (d.type === "note") return saveNote(d);   // 匿名紙條走獨立分頁
    if (!d.name) return out("skip");
    const sheet = getSheet();
    const names = sheet.getRange(2, 1, Math.max(sheet.getLastRow() - 1, 1), 1).getValues().flat();
    let row = names.indexOf(d.name) + 2;
    if (row === 1) row = sheet.getLastRow() + 1;
    sheet.getRange(row, 1, 1, HEADERS.length).setValues([[
      d.name,
      d.done ? "✅" : "",
      d.wrong || 0,
      d.doneAt ? new Date(d.doneAt) : "",
      d.lines || 0,
      d.meets || 0,
      new Date(d.ts || Date.now()),
      d.type || "",
    ]]);
    return out("ok");
  } catch (err) {
    return out("error: " + err);
  } finally {
    lock.releaseLock();
  }
}

/** 匿名紙條：對參與者匿名，主辦（本表）看得到寄件人以便審核 */
function saveNote(d) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("紙條");
  if (!sheet) {
    sheet = ss.insertSheet("紙條");
    sheet.getRange(1, 1, 1, 4)
      .setValues([["時間", "寄件人（勿外流）", "收件人", "內容"]])
      .setFontWeight("bold");
    sheet.setFrozenRows(1);
  }
  sheet.appendRow([new Date(d.ts || Date.now()), d.from || "?", d.to || "?",
    String(d.text || "").slice(0, 200)]);
  return out("ok");
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight("bold");
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function out(text) {
  return ContentService.createTextOutput(text).setMimeType(ContentService.MimeType.TEXT);
}
