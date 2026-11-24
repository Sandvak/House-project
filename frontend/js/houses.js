// Общие функции для главной, каталога и карточек объектов.
(() => {
  const staticPages = new Set(['kazansky', 'laishevo', 'volzhsky']);
  const money = new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB', maximumFractionDigits: 0
  });
  let pending;

  // Локальная копия позволяет открыть страницы в Atom без запуска сервера.
  const demoHouses = [
  {
    "id": "kazansky",
    "title": "Казанский",
    "image": "images/kazansky.webp",
    "gallery": [
      "images/kazansky.webp",
      "images/room-1.webp",
      "images/room-2.webp",
      "images/room-3.webp",
      "images/room-4.webp"
    ],
    "price": 6500000,
    "area": 120,
    "plot": 8,
    "rooms": 3,
    "floors": 1,
    "district": "Лаишевский район",
    "material": "Кирпич",
    "status": "В продаже",
    "utilities": "Электричество, вода, септик",
    "description": "Одноэтажный дом с общей кухней-гостиной и выходом в сад. Три комнаты позволяют устроить отдельную спальню, детскую и кабинет.",
    "manager": "Команда Mega House",
    "address": "",
    "plan": "images/plan-kazansky.png",
    "popularity": 3
  },
  {
    "id": "laishevo",
    "title": "Лаишево",
    "image": "images/laishevo.webp",
    "gallery": [
      "images/laishevo.webp",
      "images/room-1.webp",
      "images/room-2.webp",
      "images/room-3.webp",
      "images/room-4.webp"
    ],
    "price": 7800000,
    "area": 145,
    "plot": 10,
    "rooms": 4,
    "floors": 1,
    "district": "Лаишевский район",
    "material": "Газобетон",
    "status": "В продаже",
    "utilities": "Электричество, вода, септик",
    "description": "Просторный одноэтажный дом с четырьмя комнатами. Террасу можно обустроить как летнюю столовую, а часть участка отвести под сад.",
    "manager": "Команда Mega House",
    "address": "",
    "plan": "images/plan-laishevo.png",
    "popularity": 2
  },
  {
    "id": "volzhsky",
    "title": "Волжский",
    "image": "images/volzhsky.webp",
    "gallery": [
      "images/volzhsky.webp",
      "images/room-1.webp",
      "images/room-2.webp",
      "images/room-3.webp",
      "images/room-4.webp"
    ],
    "price": 11200000,
    "area": 180,
    "plot": 12,
    "rooms": 5,
    "floors": 2,
    "district": "Верхнеуслонский район",
    "material": "Брус",
    "status": "В продаже",
    "utilities": "Электричество, вода, септик",
    "description": "Двухэтажный семейный дом с пятью комнатами. На первом этаже расположена общая зона, на втором — тихие спальни.",
    "manager": "Команда Mega House",
    "address": "",
    "plan": "images/plan-volzhsky.png",
    "popularity": 1
  }
];

  function load() {
    if (!pending) {
      pending = location.protocol === 'file:'
        ? Promise.resolve(demoHouses)
        : fetch('http://127.0.0.1:8000/api/houses/', { headers: { Accept: 'application/json' } })
          .then(response => {
            if (!response.ok) throw new Error('Каталог недоступен');
            return response.json();
          })
          .then(items => {
            if (!Array.isArray(items)) throw new Error('Некорректный каталог');
            return items;
          })
          .catch(() => demoHouses);
    }
    return pending;
  }

  function url(id, prefix = '') {
    return staticPages.has(id)
      ? prefix + id + '.html'
      : prefix + 'house.html?id=' + encodeURIComponent(id);
  }

  function imagePath(path, prefix = '../') {
    if (!path) return '';
     if (path.startsWith('http')) return path; 
    
    if (path.startsWith('/media/')) return path;
    // Загруженные менеджером файлы отдаёт локальный сервер.
    if (path.startsWith('/media/')) return path;
    if (path.startsWith('images/')) return prefix + path;
    if (path.startsWith('/images/')) return prefix + path.slice(1);
    return '';
  }

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function card(house, assetPrefix = '../', pagePrefix = '') {
    const href = url(house.id, pagePrefix);
    const article = element('article', undefined, 'listing-card');
    const photoLink = element('a', undefined, 'listing-pic');
    photoLink.href = href;
    const photo = element('img');
    photo.src = imagePath(house.image || house.gallery?.[0], assetPrefix) || assetPrefix + 'images/kazansky.webp';
    photo.alt = 'Дом «' + house.title + '»';
    photo.loading = 'lazy';
    photoLink.append(photo);

    const heading = element('h3');
    const title = element('a', 'Дом «' + house.title + '»');
    title.href = href;
    heading.append(title);
    const specs = [house.area + ' м²', house.plot + ' сот.', house.rooms + ' комн.'];
    article.append(photoLink, element('p', house.district, 'listing-place'), heading,
      element('p', specs.join(' · '), 'listing-spec'), element('strong', money.format(house.price)));
    return article;
  }

  window.MegaHouses = { load, url, imagePath, card, money, element };
})();
