(() => {
  const form = document.getElementById('calculator');
  const request = document.getElementById('project-form');
  const total = document.getElementById('estimate');
  const summary = document.getElementById('project-summary');
  const lines = document.getElementById('estimate-lines');
  const money = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

  // 1. Словарь для связи русского названия на фронте с английским ключом на бэке
  const materialMap = {
    'Каркас': 'frame',
    'Брус': 'timber',
    'Газобетон': 'gas',
    'Кирпич': 'brick'
  };
  
  let projectDescription = '';
  let timeoutId; // Переменная для таймера задержки

  // 2. Функция стала асинхронной (async)
  async function calculate() {
    const input = new FormData(form);
    const area = Number(input.get('area'));
    
    lines.replaceChildren();
    document.getElementById('gas-note').hidden = !input.has('gas');
    
    if (!(area > 0) || !form.elements.area.validity.valid) {
      total.textContent = 'Укажите площадь';
      summary.textContent = '';
      projectDescription = '';
      return;
    }

    // Собираем данные и отправляем на Django
    const data = {
      area: area,
      material: materialMap[input.get('material')] || 'frame',
      floors: Number(input.get('floors')),
      insulation: input.has('insulation'),
      warm_floor: input.has('heat'),
      electricity: input.has('electric'),
      water: input.has('water'),
      septic: input.has('septic')
    };

    try {
      // 3. Стучимся к нашему API
      const response = await fetch('http://127.0.0.1:8000/api/constructor/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();

      // 4. Отрисовываем чек, который прислал сервер
      for (const item of result.breakdown) {
        const term = document.createElement('dt');
        const amount = document.createElement('dd');
        term.textContent = item.label;
        amount.textContent = money.format(item.value);
        lines.append(term, amount);
      }

      total.textContent = money.format(result.total_price);
      
      const floorsText = data.floors === 1 ? ' этаж' : ' этажа';
      summary.textContent = [area + ' м²', input.get('material'), data.floors + floorsText].join(' · ');
      
      // Формируем текст для заявки
      const details = result.breakdown.map(item => item.label + ': ' + money.format(item.value));
      if (input.has('gas')) details.push('Газ: стоимость уточняется');
      
      projectDescription = [summary.textContent, ...details, 'Итого: ' + total.textContent].join('\n');

    } catch (error) {
      console.error('Ошибка расчета:', error);
      total.textContent = 'Ошибка сервера';
    }
  }

  // 5. Запускаем расчет с небольшой задержкой
  form.addEventListener('input', () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(calculate, 300);
  });
  
  form.addEventListener('submit', event => event.preventDefault());
  
  request.addEventListener('submit', event => {
    if (!form.reportValidity()) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
  
  request.addEventListener('formdata', event => {
    const note = event.formData.get('comment') || '';
    event.formData.set('comment', [note.trim(), projectDescription].filter(Boolean).join('\n\n'));
  });
  
  calculate(); // Первый расчет при загрузке страницы
})();