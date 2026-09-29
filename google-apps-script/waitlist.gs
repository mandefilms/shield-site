/**
 * Shield waitlist: saves sign-ups from the website to this Google Sheet
 * and sends each new person a thank-you email from this Gmail account.
 *
 * Setup (logged in as the Gmail account the emails should come from):
 *   1. Create a Google Sheet, then Extensions > Apps Script, and paste this file in.
 *   2. Edit the settings below (Instagram link, email wording).
 *   3. Deploy > New deployment > type "Web app":
 *        Execute as: Me       Who has access: Anyone
 *   4. Approve the permissions, then copy the Web app URL into the website.
 *   After changing this file later, use Deploy > Manage deployments > Edit > New version,
 *   so the website URL stays the same.
 */

// ---- Settings -------------------------------------------------------------
const SENDER_NAME = 'Mariessa and Evan at Shield';
const INSTAGRAM_URL = 'https://www.instagram.com/YOUR_HANDLE/';
const INSTAGRAM_HANDLE = '@YOUR_HANDLE';
const SUBJECT = 'Thanks for joining the Shield family! 🛡️';
const SHEET_NAME = 'Waitlist';
// ---------------------------------------------------------------------------

const HEADERS = ['Signed up', 'Email', 'From form', 'Reply sent'];

function doPost(e) {
  const p = (e && e.parameter) || {};
  // Bots fill in the hidden field; quietly accept and ignore them
  if (p['bot-field']) return json({ ok: true });

  const email = String(p.email || '').trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254) {
    return json({ ok: false, error: 'invalid-email' });
  }
  const source = String(p.source || 'website').slice(0, 40);

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sheet = getSheet();
    const existing = sheet.getLastRow() > 1
      ? sheet.getRange(2, 2, sheet.getLastRow() - 1, 1).getValues().map(r => String(r[0]).toLowerCase())
      : [];
    // Already on the list: don't add twice or email again
    if (existing.indexOf(email) !== -1) return json({ ok: true, duplicate: true });

    sheet.appendRow([new Date(), email, source, 'Sending']);
    const row = sheet.getLastRow();
    let status;
    if (MailApp.getRemainingDailyQuota() > 0) {
      sendWelcome(email);
      status = 'Yes';
    } else {
      status = 'No (daily limit reached, run sendPendingReplies tomorrow)';
    }
    sheet.getRange(row, 4).setValue(status);
    return json({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

// Run this from the Apps Script editor to email anyone who missed out on a reply
function sendPendingReplies() {
  const sheet = getSheet();
  if (sheet.getLastRow() < 2) return;
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 4).getValues();
  rows.forEach((r, i) => {
    if (String(r[3]).indexOf('Yes') === 0) return;
    if (MailApp.getRemainingDailyQuota() < 1) return;
    sendWelcome(r[1]);
    sheet.getRange(i + 2, 4).setValue('Yes');
  });
}

function sendWelcome(email) {
  const text = [
    'Hi there,',
    '',
    "Thanks for joining the Shield family! You'll be among the first to hear about Shield.",
    '',
    "We're a small family team building Shield because we wanted a quiet, reliable way to know our kids are safe, without anyone glued to a phone. We're in the final stages of development, and we'll let you know as soon as it's ready.",
    '',
    'In the meantime, come and follow along on Instagram, where we share behind-the-scenes looks at the design, sneak peeks of the Shields and docks, and updates as we get closer to launch.',
    '',
    'Follow us on Instagram: ' + INSTAGRAM_HANDLE + ' ' + INSTAGRAM_URL,
    '',
    "We promise we hate spam too. We'll only email when it matters.",
    '',
    'Mariessa and Evan',
    'Auntie Reesa and Uncle Evan, Founders of Shield',
    '',
    "Don't want these emails? Just reply with \"unsubscribe\" and we'll remove you."
  ].join('\n');

  const html =
    '<div style="font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:#1A2B40;max-width:520px">' +
    '<p>Hi there,</p>' +
    "<p>Thanks for joining the <strong>Shield family</strong>! You'll be among the first to hear about Shield.</p>" +
    "<p>We're a small family team building Shield because we wanted a quiet, reliable way to know our kids are safe, without anyone glued to a phone. We're in the final stages of development, and we'll let you know as soon as it's ready.</p>" +
    '<p>In the meantime, come and follow along on Instagram, where we share behind-the-scenes looks at the design, sneak peeks of the Shields and docks, and updates as we get closer to launch.</p>' +
    '<p><a href="' + INSTAGRAM_URL + '" style="display:inline-block;background:#FF6B6B;color:#ffffff;text-decoration:none;padding:10px 20px;border-radius:100px;font-weight:bold">Follow ' + INSTAGRAM_HANDLE + ' on Instagram</a></p>' +
    "<p>We promise we hate spam too. We'll only email when it matters.</p>" +
    '<p>Mariessa and Evan<br><span style="color:#3A5472">Auntie Reesa and Uncle Evan, Founders of Shield</span></p>' +
    '<p style="font-size:12px;color:#8A97A8">Don\'t want these emails? Just reply with "unsubscribe" and we\'ll remove you.</p>' +
    '</div>';

  MailApp.sendEmail({ to: email, subject: SUBJECT, body: text, htmlBody: html, name: SENDER_NAME });
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
  }
  return sheet;
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Optional: run this once from the editor to check the email looks right (sends to this account)
function sendTestEmailToMe() {
  sendWelcome(Session.getActiveUser().getEmail());
}
