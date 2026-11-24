// Общее поведение страниц: меню, заявки и выбор статистики.
'use strict';

const menuButton = document.querySelector('.menu-toggle');
const menu = document.querySelector('#site-menu');

function toggleMenu(open) {
  menu.classList.toggle('open', open);
  menuButton.setAttribute('aria-expanded', String(open));
}
menuButton?.addEventListener('click', () => toggleMenu(!menu.classList.contains('open')));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu?.classList.contains('open')) {
    toggleMenu(false);
    menuButton.focus();
  }
});

const isServer = location.protocol === 'http:' || location.protocol === 'https:';
const cookieDialog = document.querySelector('#cookie-settings');

async function recordVisit() {
  if (!isServer) return;
  try {
    await fetch('/api/visit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
    });
  } catch {
    // Статистика не должна прерывать работу со страницей.
  }
}
document.querySelector('[data-cookie-settings]')?.addEventListener('click', () => {
  cookieDialog.returnValue = '';
  cookieDialog.showModal();
});
cookieDialog?.addEventListener('close', () => {
  if (!['yes', 'no'].includes(cookieDialog.returnValue)) return;
  try { localStorage.setItem('mega-house-stats', cookieDialog.returnValue); } catch { /* Только на время просмотра. */ }
  if (cookieDialog.returnValue === 'yes') recordVisit();
});
try {
  if (localStorage.getItem('mega-house-stats') === 'yes') recordVisit();
} catch { /* Некоторые браузеры ограничивают доступ при открытии файлов. */ }

function validatePhone(input) {
  const number = input.value.trim();
  const digits = number.replace(/\D/g, '');
  const valid = /^\+?[\d\s()-]+$/.test(number) && digits.length >= 7 && digits.length <= 15;
  input.setCustomValidity(valid ? '' : 'Введите телефон с кодом города или страны: от 7 до 15 цифр.');
  return valid;
}
for (const form of document.querySelectorAll('.lead-form')) {
  const phone = form.elements.phone;
  const status = form.querySelector('[role="status"]');
  phone.addEventListener('input', () => phone.setCustomValidity(''));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!validatePhone(phone)) {
      phone.reportValidity();
      return;
    }
    if (!isServer) {
      status.textContent = 'Форма проверена. Чтобы сохранить учебную заявку, запустите файл start-windows.bat и откройте сайт по адресу из окна запуска.';
      return;
    }
    const button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    button.disabled = true;
    try {
      const lead = Object.fromEntries(new FormData(form));
     lead.consent = form.elements.agree.checked;
    lead.type = "consult";
      const response = await fetch('/api/leads', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(lead)
      });
      if (!response.headers.get('content-type')?.includes('application/json')) {
        throw new Error('Запустите проект через start-windows.bat, чтобы сохранять заявки.');
      }
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Не удалось сохранить заявку.');
      status.textContent = 'Спасибо! Учебная заявка сохранена. Она доступна команде в разделе «Заявки».';
      form.reset();
    } catch (error) {
      status.textContent = error.message || 'Сервер недоступен. Попробуйте ещё раз.';
    } finally {
      button.disabled = false;
    }
  });
}

async function updatePageText() {
  const paragraphs = document.querySelectorAll('[data-content]');
  if (!isServer || !paragraphs.length) return;
  try {
    const response = await fetch('/api/content');
    if (!response.ok) return;
    const changes = await response.json();
    for (const paragraph of paragraphs) {
      const text = changes[paragraph.dataset.content];
      if (typeof text === 'string' && text.trim()) paragraph.textContent = text;
    }
  } catch { /* По умолчанию показан текст из HTML. */ }
}
updatePageText();

// На главной оставляем три самых популярных доступных объекта.
async function updateFeatured() {
  const container = document.querySelector('#featured-houses');
  if (!container || !isServer || !window.MegaHouses) return;
  const houses = await MegaHouses.load();
  const template = container.firstElementChild;
  const featured = houses.slice().sort((a, b) => b.popularity - a.popularity).slice(0, 3);
  const cards = featured.map(house => {
    const card = template.cloneNode(true);
    const title = 'Дом «' + house.title + '»';
    for (const anchor of card.querySelectorAll('a')) anchor.href = MegaHouses.url(house.id, 'page/');
    card.querySelector('.photo-link').setAttribute('aria-label', 'Открыть ' + title);
    const image = card.querySelector('img');
    image.src = MegaHouses.imagePath(house.image, '') || 'images/hero.webp';
    image.alt = title;
    card.querySelector('.location').textContent = house.district;
    card.querySelector('h3 a').textContent = title;
    card.querySelector('.feature-info p').textContent = house.area + ' м² · ' + house.rooms + ' комн.';
    card.querySelector('strong').textContent = MegaHouses.money.format(house.price);
    return card;
  });
  container.replaceChildren(...cards);
  if (!cards.length) container.textContent = 'Новые дома скоро появятся в каталоге.';
}
updateFeatured();

const cookieNotice = document.querySelector('.cookie-notice');
if (cookieNotice && isServer) {
  try { cookieNotice.hidden = Boolean(localStorage.getItem('mega-house-stats')); } catch { cookieNotice.hidden = true; }
  cookieNotice.addEventListener('click', event => {
    const choice = event.target.closest('[data-cookie-choice]')?.dataset.cookieChoice;
    if (!choice) return;
    try { localStorage.setItem('mega-house-stats', choice); } catch { /* Выбор действует на этой странице. */ }
    if (choice === 'yes') recordVisit();
    cookieNotice.hidden = true;
  });
  cookieDialog?.addEventListener('close', () => {
    if (['yes', 'no'].includes(cookieDialog.returnValue)) cookieNotice.hidden = true;
  });
}
