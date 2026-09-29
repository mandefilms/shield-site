/**
 * Shield waitlist: saves sign-ups from the website to this Google Sheet
 * and sends each new person a thank-you email from this Gmail account.
 *
 * Setup (logged in as the Gmail account the emails should come from):
 *   1. Either create a Google Sheet and open Extensions > Apps Script, or go straight to
 *      script.google.com and click "New project". Paste this file in.
 *      (If started on its own, the script creates a "Shield waitlist" sheet in your Drive.)
 *   2. Check the settings below (Instagram link, email wording).
 *   3. Deploy > New deployment > type "Web app":
 *        Execute as: Me       Who has access: Anyone
 *   4. Approve the permissions, then copy the Web app URL into the website.
 *   After changing this file later, use Deploy > Manage deployments > Edit > New version,
 *   so the website URL stays the same.
 */

// ---- Settings -------------------------------------------------------------
const SENDER_NAME = 'Mariessa and Evan at Shield';
const INSTAGRAM_URL = 'https://www.instagram.com/mya.shield/';
const INSTAGRAM_HANDLE = '@mya.shield';
const SUBJECT = 'Thanks for joining the Shield family! 🛡️';
const SHEET_NAME = 'Waitlist';
const PRIVACY_URL = 'https://myashield.netlify.app/privacy.html';
// Sign-up alerts for you: 'instant' (an email for each new sign-up), 'daily' (one summary a day,
// run setupDailySummary once to switch it on) or 'off'. Alerts share Gmail's ~100 emails/day limit.
const NOTIFY_MODE = 'instant';
const NOTIFY_EMAIL = 'contact.myashield@gmail.com';
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
      try {
        sendWelcome(email);
        status = 'Yes';
      } catch (err) {
        // The sign-up is still saved; this can be retried with sendPendingReplies
        status = 'No (email failed: ' + err.message + ')';
      }
    } else {
      status = 'No (daily limit reached, run sendPendingReplies tomorrow)';
    }
    sheet.getRange(row, 4).setValue(status);
    // Welcome emails come first: alerts pause when fewer than 20 emails are left for the day
    if (NOTIFY_MODE === 'instant' && MailApp.getRemainingDailyQuota() > 20) {
      try { notifyNewSignup(email, source, row - 1); } catch (err) { /* an alert failing never blocks a sign-up */ }
    }
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

function notifyNewSignup(email, source, total) {
  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: 'New Shield sign-up: ' + email,
    body: email + ' just joined the Shield waitlist (from the ' + source + ' form).\n\n' +
      'People on the list: ' + total + '\n' + getSpreadsheet().getUrl(),
    name: 'Shield waitlist'
  });
}

// Daily summary: run setupDailySummary once from the editor (with NOTIFY_MODE = 'daily')
function setupDailySummary() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'sendDailySummary')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('sendDailySummary').timeBased().everyDays(1).atHour(8).create();
  PropertiesService.getScriptProperties().setProperty('SUMMARY_FROM_ROW', String(getSheet().getLastRow() + 1));
}

function sendDailySummary() {
  const sheet = getSheet();
  const props = PropertiesService.getScriptProperties();
  const from = Number(props.getProperty('SUMMARY_FROM_ROW') || 2);
  const last = sheet.getLastRow();
  if (last < from || MailApp.getRemainingDailyQuota() < 1) return;
  const emails = sheet.getRange(from, 2, last - from + 1, 1).getValues().map(r => r[0]);
  MailApp.sendEmail({
    to: NOTIFY_EMAIL,
    subject: emails.length + ' new Shield sign-up' + (emails.length === 1 ? '' : 's'),
    body: 'New since the last summary:\n\n' + emails.join('\n') + '\n\nPeople on the list: ' + (last - 1) + '\n' + getSpreadsheet().getUrl(),
    name: 'Shield waitlist'
  });
  props.setProperty('SUMMARY_FROM_ROW', String(last + 1));
}

function sendWelcome(email) {
  const text = [
    'Hi there,',
    '',
    "Thanks for joining the Shield family! You'll be among the first to hear about Shield.",
    '',
    "We're in the final stages of development, and we'll let you know as soon as it's ready.",
    '',
    'In the meantime, follow our Instagram to learn more about Shield, child safety and who we are!',
    '',
    'Follow us on Instagram: ' + INSTAGRAM_HANDLE + ' ' + INSTAGRAM_URL,
    '',
    "We promise we hate spam too. We'll only email when it matters.",
    '',
    'Mariessa and Evan',
    'Auntie Reesa and Uncle Evan, Founders of Shield',
    '',
    "Don't want these emails? Just reply with \"unsubscribe\" and we'll remove you.",
    'Privacy policy: ' + PRIVACY_URL
  ].join('\n');

  const html =
    '<div style="font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.6;color:#1A2B40;max-width:520px">' +
    '<p>Hi there,</p>' +
    "<p>Thanks for joining the <strong>Shield family</strong>! You'll be among the first to hear about Shield.</p>" +
    "<p>We're in the final stages of development, and we'll let you know as soon as it's ready.</p>" +
    '<p>In the meantime, follow our Instagram to learn more about Shield, child safety and who we are!</p>' +
    '<p><a href="' + INSTAGRAM_URL + '" style="display:inline-block;background:#FF6B6B;color:#ffffff;text-decoration:none;padding:10px 20px;border-radius:100px;font-weight:bold">Follow ' + INSTAGRAM_HANDLE + ' on Instagram</a></p>' +
    "<p>We promise we hate spam too. We'll only email when it matters.</p>" +
    '<p>Mariessa and Evan<br><span style="color:#3A5472">Auntie Reesa and Uncle Evan, Founders of Shield</span></p>' +
    '<p style="font-size:12px;color:#8A97A8">Don\'t want these emails? Just reply with "unsubscribe" and we\'ll remove you.<br><a href="' + PRIVACY_URL + '" style="color:#8A97A8">Privacy policy</a></p>' +
    '</div>';

  MailApp.sendEmail({ to: email, subject: SUBJECT, body: text, htmlBody: html, name: SENDER_NAME });
}

// Works whether the script lives inside a sheet or on its own at script.google.com
function getSpreadsheet() {
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) return active;
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('SHEET_ID');
  if (id) return SpreadsheetApp.openById(id);
  const created = SpreadsheetApp.create('Shield waitlist');
  props.setProperty('SHEET_ID', created.getId());
  return created;
}

// Run this once from the editor to create the sheet (if needed) and get its link in the log
function showSheetLink() {
  Logger.log(getSpreadsheet().getUrl());
}

function getSheet() {
  const ss = getSpreadsheet();
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
