const copy = {
  fa: { brand: 'همراه پشتیبانی', brandNote: 'پاسخ‌گو، هر زمان', connecting: 'در حال اتصال…', offline: 'حالت آفلاین', llm: 'پشتیبانی هوشمند آنلاین', unavailable: 'ارتباط برقرار نشد', eyebrow: 'پشتیبانی هوشمند', headline: 'چطور می‌توانیم کمکتان کنیم؟', intro: 'سؤالتان را بنویسید؛ دستیار از راهنمای پشتیبانی پاسخ می‌دهد و اگر مطمئن نباشد، صادقانه می‌گوید.', suggestions: 'برای شروع، یکی از این‌ها را بپرسید', privacy: 'پرسش‌های بی‌پاسخ برای بهبود راهنمای پشتیبانی ثبت می‌شوند.', assistant: 'دستیار پشتیبانی', online: 'آماده پاسخ‌گویی', newChat: 'گفت‌وگوی تازه', welcome: 'سلام! من دستیار پشتیبانی هستم. درباره سفارش، ارسال یا محصولات هر سؤالی دارید بپرسید.', now: 'همین حالا', inputLabel: 'پیام شما', placeholder: 'پیامتان را اینجا بنویسید…', send: 'ارسال', composerNote: 'Enter برای ارسال · Shift + Enter برای خط جدید', footer: 'پاسخ‌ها بر اساس اطلاعات راهنمای پشتیبانی ارائه می‌شوند.', apiDocs: 'مستندات API', typing: 'در حال نوشتن…', error: 'پاسخی دریافت نشد. اتصال را بررسی کنید و دوباره تلاش کنید.', sources: 'منابع پاسخ', clearError: 'گفت‌وگو پاک نشد؛ دوباره تلاش کنید.', resetWelcome: 'گفت‌وگوی تازه شروع شد. چطور می‌توانم کمکتان کنم؟' },
  en: { brand: 'Support Companion', brandNote: 'Here whenever you need us', connecting: 'Connecting…', offline: 'Offline mode', llm: 'AI support online', unavailable: 'Connection unavailable', eyebrow: 'AI SUPPORT', headline: 'How can we help you today?', intro: 'Ask a question and the assistant will answer from the support guide. If it is unsure, it will say so.', suggestions: 'Try asking one of these', privacy: 'Unanswered questions may be logged to improve the support guide.', assistant: 'Support assistant', online: 'Ready to help', newChat: 'New chat', welcome: 'Hi! I’m your support assistant. Ask me about orders, shipping, or products.', now: 'Just now', inputLabel: 'Your message', placeholder: 'Write your message here…', send: 'Send', composerNote: 'Enter to send · Shift + Enter for a new line', footer: 'Answers are based on the support knowledge base.', apiDocs: 'API docs', typing: 'Thinking…', error: 'No response received. Check your connection and try again.', sources: 'Answer sources', clearError: 'The conversation could not be cleared. Please try again.', resetWelcome: 'A new conversation has started. How can I help?' }
};

const $ = (selector) => document.querySelector(selector);
const messages = $('#messages');
const form = $('#chat-form');
const input = $('#message-input');
const sendButton = $('#send-button');
const errorBox = $('#chat-error');
const modePill = $('#mode-pill');
let language = 'fa';
let sessionId = newSessionId();
let busy = false;

function newSessionId() {
  return globalThis.crypto?.randomUUID?.() ?? `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function text(key) { return copy[language][key]; }
function translate() {
  document.documentElement.lang = language;
  document.documentElement.dir = language === 'fa' ? 'rtl' : 'ltr';
  document.querySelectorAll('[data-i18n]').forEach((element) => { element.textContent = text(element.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => { element.placeholder = text(element.dataset.i18nPlaceholder); });
  document.querySelectorAll('.suggestion').forEach((button) => { button.firstChild.textContent = language === 'fa' ? button.dataset.questionFa : button.dataset.questionEn; });
  $('#language-toggle').textContent = language === 'fa' ? 'EN' : 'فا';
}

function addMessage(content, role, sources = []) {
  const article = document.createElement('article');
  article.className = `message message--${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.textContent = content;
  article.append(bubble);
  if (sources.length) {
    const details = document.createElement('details');
    details.className = 'sources';
    const summary = document.createElement('summary');
    summary.textContent = `${text('sources')} (${sources.length})`;
    const list = document.createElement('ul');
    sources.forEach((source) => { const item = document.createElement('li'); item.textContent = source; list.append(item); });
    details.append(summary, list);
    article.append(details);
  }
  const time = document.createElement('time');
  time.dateTime = new Date().toISOString();
  time.textContent = text('now');
  article.append(time);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  input.disabled = value;
  sendButton.setAttribute('aria-busy', String(value));
}

async function sendMessage(value) {
  const message = value.trim();
  if (!message || busy) return;
  errorBox.hidden = true;
  addMessage(message, 'user');
  input.value = '';
  input.style.height = 'auto';
  setBusy(true);
  const typing = addMessage(text('typing'), 'assistant');
  typing.classList.add('typing');
  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });
    if (!response.ok) throw new Error(`Chat request failed (${response.status})`);
    const reply = await response.json();
    typing.remove();
    addMessage(reply.answer, 'assistant', reply.sources ?? []);
    modePill.textContent = reply.mode === 'llm' ? text('llm') : text('offline');
  } catch {
    typing.remove();
    errorBox.textContent = text('error');
    errorBox.hidden = false;
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener('submit', (event) => { event.preventDefault(); sendMessage(input.value); });
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 120)}px`; });
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
});
document.querySelectorAll('.suggestion').forEach((button) => button.addEventListener('click', () => sendMessage(language === 'fa' ? button.dataset.questionFa : button.dataset.questionEn)));
$('#language-toggle').addEventListener('click', () => { language = language === 'fa' ? 'en' : 'fa'; translate(); });
$('#reset-chat').addEventListener('click', async () => {
  if (busy) return;
  const oldSessionId = sessionId;
  setBusy(true);
  errorBox.hidden = true;
  try {
    const response = await fetch(`/chat/${encodeURIComponent(oldSessionId)}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Could not reset chat');
    sessionId = newSessionId();
    messages.replaceChildren();
    addMessage(text('resetWelcome'), 'assistant');
  } catch {
    errorBox.textContent = text('clearError');
    errorBox.hidden = false;
  } finally { setBusy(false); input.focus(); }
});

translate();
fetch('/health').then((response) => response.ok ? response.json() : Promise.reject()).then((health) => {
  modePill.textContent = health.mode === 'llm' ? text('llm') : text('offline');
}).catch(() => { modePill.textContent = text('unavailable'); });
