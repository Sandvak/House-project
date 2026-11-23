(async () => {
  const { load, money, imagePath, element, card } = window.MegaHouses;
  const property = document.getElementById('property');
  const id = property.dataset.id || new URLSearchParams(location.search).get('id');
  const all = await load();
  const house = all.find(item => item.id === id);
  if (!house) {
    const back = element('a', 'Вернуться в каталог', 'button');
    back.href = 'catalog.html';
    document.querySelector('main').replaceChildren(element('h1', 'Дом не найден'), back);
    document.title = 'Дом не найден | Mega House';
    return;
  }
  const heading = 'Дом «' + house.title + '»';
  const info = {
    ...house, heading, price: money.format(house.price), area: house.area + ' м²',
    plot: house.plot + ' сот.', location: house.address || 'Республика Татарстан, ' + house.district
  };
  document.title = heading + ' | Mega House';
  document.querySelector('.crumbs span:last-child').textContent = heading;
  for (const node of document.querySelectorAll('[data-house]')) {
    node.textContent = info[node.dataset.house] || 'Уточняется';
  }
  document.querySelectorAll('input[name="house"]').forEach(input => {
    input.value = house.id;
    input.defaultValue = house.id;
  });
  const specs = {
    area: 'Площадь дома', plot: 'Участок', rooms: 'Комнаты', floors: 'Этажность',
    material: 'Материал', utilities: 'Коммуникации', status: 'Статус'
  };
  const facts = document.getElementById('house-facts');
  facts.replaceChildren();
  for (const [key, label] of Object.entries(specs)) {
    facts.append(element('dt', label), element('dd', info[key] || 'Уточняется'));
  }
  const map = new URL('https://yandex.ru/maps/');
  map.searchParams.set('text', info.location);
  document.getElementById('map-link').href = map.href;
  const related = all.filter(other => other.id !== id).slice(0, 3);
  document.getElementById('similar').hidden = related.length === 0;
  document.getElementById('similar-list').replaceChildren(...related.map(other => card(other)));

  const planPath = imagePath(house.plan);
  document.getElementById('floor-plan').hidden = !planPath;
  if (planPath) {
    document.getElementById('plan-image').src = planPath;
    document.getElementById('plan-image').alt = 'Планировка дома «' + house.title + '»';
  }
  const images = [...new Set([house.image, ...(house.gallery || [])].map(path => imagePath(path)).filter(Boolean))];
  if (!images.length) images.push('../images/kazansky.webp');
  const cover = document.getElementById('cover-photo');
  cover.src = images[0];
  cover.alt = heading;
  const dialog = document.getElementById('photo-dialog');
  const thumbs = document.getElementById('thumbs');
  let currentPhoto = 0;

  function showPhoto(index) {
    currentPhoto = (index + images.length) % images.length;
    const photo = document.getElementById('large-photo');
    photo.src = images[currentPhoto];
    photo.alt = heading + ', фотография ' + (currentPhoto + 1);
    document.getElementById('photo-count').textContent = (currentPhoto + 1) + ' из ' + images.length;
    if (!dialog.open) {
      dialog.showModal();
      document.getElementById('close-photo').focus();
    }
  }

  thumbs.replaceChildren();
  images.forEach((path, i) => {
    const button = element('button');
    button.type = 'button';
    button.setAttribute('aria-label', 'Открыть фото ' + (i + 1));
    const image = element('img');
    image.src = path;
    image.alt = '';
    image.loading = 'lazy';
    button.append(image);
    button.addEventListener('click', () => showPhoto(i));
    thumbs.append(button);
  });
  document.querySelector('.main-photo').addEventListener('click', () => showPhoto(0));
  document.getElementById('close-photo').addEventListener('click', () => dialog.close());
  document.getElementById('prev-photo').addEventListener('click', () => showPhoto(currentPhoto - 1));
  document.getElementById('next-photo').addEventListener('click', () => showPhoto(currentPhoto + 1));
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') showPhoto(currentPhoto - 1);
    if (event.key === 'ArrowRight') showPhoto(currentPhoto + 1);
  });
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });

  document.getElementById('share').addEventListener('click', async () => {
    const state = document.getElementById('share-status');
    const link = new URL(location.href);
    link.hash = '';
    try {
      if (navigator.share) await navigator.share({ title: heading, url: link.href });
      else {
        await navigator.clipboard.writeText(link.href);
        state.textContent = 'Ссылка скопирована';
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        state.textContent = 'Ссылка на дом: ' + link.href;
      }
    }
  });

  function openQuestion() {
    if (location.hash === '#question') document.getElementById('question').open = true;
  }
  window.addEventListener('hashchange', openQuestion);
  openQuestion();
})();
