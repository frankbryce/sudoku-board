/**
 * DoDad Puzzles™ — Mailing List Google Apps Script Backend
 *
 * Stores email signups from https://dodadpuzzles.com in a Google Sheet
 * and maintains a ready-to-copy "Gmail BCC" tab for one-click copy/paste.
 *
 * Setup instructions: see mailing-list/README.md
 */

const SUBSCRIBERS_SHEET = "Subscribers";
const BCC_SHEET = "Gmail BCC";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/**
 * Run this function ONCE from the Apps Script editor (Run -> setupSheet)
 * to create and format the "Subscribers" and "Gmail BCC" tabs.
 */
function setupSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 1. Subscribers tab
  let subSheet = ss.getSheetByName(SUBSCRIBERS_SHEET);
  if (!subSheet) {
    subSheet = ss.getSheets()[0];
    subSheet.setName(SUBSCRIBERS_SHEET);
  }

  if (subSheet.getLastRow() === 0) {
    subSheet.appendRow(["Timestamp", "Email", "Interests", "Source", "Status"]);
    subSheet.getRange("A1:E1").setFontWeight("bold");
    subSheet.setFrozenRows(1);
    subSheet.setColumnWidth(1, 180);
    subSheet.setColumnWidth(2, 260);
    subSheet.setColumnWidth(3, 240);
    subSheet.setColumnWidth(4, 130);
    subSheet.setColumnWidth(5, 100);
  }

  // 2. Gmail BCC tab (ready-to-copy comma-separated lists)
  let bccSheet = ss.getSheetByName(BCC_SHEET);
  if (!bccSheet) {
    bccSheet = ss.insertSheet(BCC_SHEET);
  }

  bccSheet.clear();
  bccSheet.getRange("A1:C1").setValues([["Segment", "Active Count", "Copy & Paste into Gmail BCC"]]);
  bccSheet.getRange("A1:C1").setFontWeight("bold");
  bccSheet.setFrozenRows(1);

  bccSheet.getRange("A2:C4").setValues([
    [
      "All Active Subscribers",
      '=COUNTIF(Subscribers!E2:E, "active")',
      '=IFERROR(TEXTJOIN(", ", TRUE, UNIQUE(FILTER(Subscribers!B2:B, Subscribers!B2:B<>"", LOWER(Subscribers!E2:E)="active"))), "")',
    ],
    [
      "Shipped 4x4 Kits",
      '=COUNTIFS(Subscribers!E2:E, "active", Subscribers!C2:C, "*shipped-kits*")',
      '=IFERROR(TEXTJOIN(", ", TRUE, UNIQUE(FILTER(Subscribers!B2:B, Subscribers!B2:B<>"", LOWER(Subscribers!E2:E)="active", ISNUMBER(SEARCH("shipped-kits", Subscribers!C2:C))))), "")',
    ],
    [
      "New Free Puzzles & STLs",
      '=COUNTIFS(Subscribers!E2:E, "active", Subscribers!C2:C, "*free-puzzles*")',
      '=IFERROR(TEXTJOIN(", ", TRUE, UNIQUE(FILTER(Subscribers!B2:B, Subscribers!B2:B<>"", LOWER(Subscribers!E2:E)="active", ISNUMBER(SEARCH("free-puzzles", Subscribers!C2:C))))), "")',
    ],
  ]);

  bccSheet.setColumnWidth(1, 220);
  bccSheet.setColumnWidth(2, 120);
  bccSheet.setColumnWidth(3, 520);
  bccSheet.getRange("C2:C4").setWrap(true);
}

/**
 * Handles POST requests from the dodadpuzzles.com signup forms.
 * Accepts both application/x-www-form-urlencoded (FormData/URLSearchParams)
 * and text/plain JSON payloads without triggering a CORS preflight.
 */
function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);

    const payload = parsePayload_(e);

    // Honeypot check: silently accept to avoid tipping off bots, without saving.
    if (payload.website) {
      return jsonResponse_({ ok: true, status: "subscribed" });
    }

    const email = (payload.email || "").trim().toLowerCase();
    if (!email || email.length > 254 || !EMAIL_RE.test(email)) {
      return jsonResponse_({
        ok: false,
        error: "Please enter a valid email address.",
      });
    }

    const interests = normalizeInterests_(payload.interests);
    const source = (payload.source || "website").trim().slice(0, 64);

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let subSheet = ss.getSheetByName(SUBSCRIBERS_SHEET);
    if (!subSheet) {
      setupSheet();
      subSheet = ss.getSheetByName(SUBSCRIBERS_SHEET);
    }

    const now = new Date();
    const lastRow = subSheet.getLastRow();

    // Check if email already exists (deduplicate & merge interests)
    if (lastRow >= 2) {
      const existingRows = subSheet.getRange(2, 1, lastRow - 1, 5).getValues();
      for (let i = 0; i < existingRows.length; i++) {
        const rowEmail = String(existingRows[i][1] || "").trim().toLowerCase();
        if (rowEmail === email) {
          const prevInterests = String(existingRows[i][2] || "")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
          const merged = Array.from(new Set([...prevInterests, ...interests])).join(", ");
          const rowNum = i + 2;
          subSheet.getRange(rowNum, 1).setValue(now);
          subSheet.getRange(rowNum, 3).setValue(merged);
          subSheet.getRange(rowNum, 5).setValue("active");
          return jsonResponse_({ ok: true, status: "updated" });
        }
      }
    }

    subSheet.appendRow([now, email, interests.join(", "), source, "active"]);
    return jsonResponse_({ ok: true, status: "subscribed" });
  } catch (err) {
    return jsonResponse_({
      ok: false,
      error: "Could not save your signup right now. Please try again in a moment.",
    });
  } finally {
    lock.releaseLock();
  }
}

/**
 * Simple health-check endpoint for verifying deployment in a browser.
 */
function doGet() {
  return jsonResponse_({ ok: true, service: "DoDad Puzzles Mailing List" });
}

function parsePayload_(e) {
  if (!e) return {};

  // Form-encoded submission (e.parameter / e.parameters)
  if (e.parameter && Object.keys(e.parameter).length > 0) {
    const interestsParam =
      (e.parameters && e.parameters.interests) ||
      (e.parameter.interests ? [e.parameter.interests] : []);
    return {
      email: e.parameter.email || "",
      interests: interestsParam,
      source: e.parameter.source || "website",
      website: e.parameter.website || "",
    };
  }

  // Raw JSON body (e.g. text/plain JSON)
  if (e.postData && e.postData.contents) {
    try {
      return JSON.parse(e.postData.contents);
    } catch (_) {
      return {};
    }
  }

  return {};
}

function normalizeInterests_(raw) {
  const allowed = new Set(["shipped-kits", "free-puzzles"]);
  const list = Array.isArray(raw)
    ? raw
    : String(raw || "")
        .split(",")
        .map((s) => s.trim());
  return Array.from(new Set(list.filter((item) => allowed.has(item))));
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
