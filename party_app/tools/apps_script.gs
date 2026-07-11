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

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000); // 53 人同時操作時避免互相蓋寫
  try {
    const d = JSON.parse(e.postData.contents);
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
