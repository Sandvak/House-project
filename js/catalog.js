(async () => {
  const { load, card, element } = window.MegaHouses;
  const houses = await load();
  const form = document.getElementById('filters');
  const details = document.getElementById('filter-details');
  const pagination = document.getElementById('pagination');
  const pageSize = 6;

  // Дополнительные значения появляются здесь после создания объекта в админке.
  for (const key of ['district', 'material', 'floors', 'rooms']) {
    const select = form.elements[key];
    const values = new Set(Array.from(select.options, option => option.value));
    for (const house of houses) {
      const value = String(house[key] ?? '');
      if (value && !values.has(value)) {
        select.add(new Option(value, value));
        values.add(value);
      }
    }
  }

  function fillFromUrl() {
    const params = new URLSearchParams(location.search);
    for (const field of form.elements) {
      if (!field.name) continue;
      field.value = params.get(field.name) ?? (field.name === 'sort' ? 'popular' : '');
      if (field.closest('details') && field.value) details.open = true;
    }
    return params;
  }

  function keep(house, params) {
    const term = (params.get('q') || '').trim().toLocaleLowerCase('ru');
    if (!('Дом ' + house.title + ' ' + house.district).toLocaleLowerCase('ru').includes(term)) return false;
    for (const key of ['district', 'material', 'floors', 'rooms']) {
      if (params.get(key) && String(house[key]) !== params.get(key)) return false;
    }
    for (const key of ['price', 'area', 'plot']) {
      if (params.get(key + '_min') && Number(house[key]) < Number(params.get(key + '_min'))) return false;
      if (params.get(key + '_max') && Number(house[key]) > Number(params.get(key + '_max'))) return false;
    }
    return true;
  }

  function render() {
    const params = fillFromUrl();
    const sorted = houses.filter(house => keep(house, params)).sort((a, b) => {
      switch (params.get('sort')) {
        case 'price_asc': return a.price - b.price;
        case 'price_desc': return b.price - a.price;
        case 'area': return a.area - b.area;
        default: return (b.popularity || 0) - (a.popularity || 0);
      }
    });
    const pageCount = Math.ceil(sorted.length / pageSize);
    const requested = Number.parseInt(params.get('page'), 10) || 1;
    const page = Math.max(1, Math.min(requested, pageCount));
    document.getElementById('house-list').replaceChildren(
      ...sorted.slice((page - 1) * pageSize, page * pageSize).map(house => card(house))
    );
    document.getElementById('result-count').textContent = 'Объектов: ' + sorted.length;
    document.getElementById('no-results').hidden = sorted.length > 0;
    pagination.replaceChildren();
    if (pageCount > 1) {
      for (let index = 1; index <= pageCount; index++) {
        const link = element('a', String(index));
        const next = new URL(location.href);
        next.searchParams.set('page', index);
        link.href = next.href;
        link.setAttribute('aria-label', 'Страница ' + index);
        if (page === index) link.setAttribute('aria-current', 'page');
        pagination.append(link);
      }
    }
  }

  function navigate(url) {
    try {
      history.pushState(null, '', url);
      render();
    } catch {
      location.assign(url);
    }
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    const error = document.getElementById('filter-error');
    error.textContent = '';
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form)) {
      if (value.trim() && !(key === 'sort' && value === 'popular')) params.set(key, value.trim());
    }
    for (const key of ['price', 'area', 'plot']) {
      const low = params.get(key + '_min'), high = params.get(key + '_max');
      if (low && high && Number(low) > Number(high)) {
        details.open = true;
        form.elements[key + '_max'].focus();
        error.textContent = 'Верхняя граница диапазона должна быть не меньше нижней.';
        return;
      }
    }
    const url = new URL(location.href);
    url.search = params.toString();
    navigate(url);
  });
  document.getElementById('filter-reset').addEventListener('click', event => {
    event.preventDefault();
    document.getElementById('filter-error').textContent = '';
    const url = new URL(location.href);
    url.search = '';
    navigate(url);
  });
  window.addEventListener('popstate', render);
  render();
})();
