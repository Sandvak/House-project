(() => {
  const form = document.getElementById('calculator');
  const request = document.getElementById('project-form');
  const total = document.getElementById('estimate');
  const summary = document.getElementById('project-summary');
  const lines = document.getElementById('estimate-lines');
  const money = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

  // Все тарифы из ТЗ. Первые три стоимости зависят от площади дома.
  const rates = {
    'Каркас': { base: 25000, insulation: 3000, heat: 3500 },
    'Брус': { base: 35000, insulation: 4000, heat: 3500 },
    'Газобетон': { base: 50000, insulation: 4000, heat: 5000 },
    'Кирпич': { base: 80000, insulation: 4000, heat: 5000 }
  };
  const fixed = {
    electric: ['Электричество', 150000],
    water: ['Вода', 250000],
    septic: ['Септик', 200000]
  };
  let projectDescription = '';

  function calculate() {
    const input = new FormData(form);
    const area = Number(input.get('area'));
    const valid = area > 0 && form.elements.area.validity.valid;
    lines.replaceChildren();
    document.getElementById('gas-note').hidden = !input.has('gas');
    if (!valid) {
      total.textContent = 'Укажите площадь';
      summary.textContent = '';
      projectDescription = '';
      return;
    }
    const material = input.get('material');
    const floors = Number(input.get('floors'));
    const rate = rates[material];
    const breakdown = [['Базовая стоимость', area * rate.base]];
    if (floors === 1) breakdown.push(['Скидка за один этаж (5 %)', -area * rate.base * 0.05]);
    if (input.has('insulation')) breakdown.push(['Утепление', area * rate.insulation]);
    if (input.has('heat')) breakdown.push(['Тёплый пол', area * rate.heat]);
    for (const [key, item] of Object.entries(fixed)) {
      if (input.has(key)) breakdown.push(item);
    }
    let sum = 0;
    for (const [label, value] of breakdown) {
      sum += value;
      const term = document.createElement('dt');
      const amount = document.createElement('dd');
      term.textContent = label;
      amount.textContent = money.format(value);
      lines.append(term, amount);
    }
    total.textContent = money.format(sum);
    summary.textContent = [area + ' м²', material, floors + (floors === 1 ? ' этаж' : ' этажа')].join(' · ');
    const details = breakdown.map(([label, value]) => label + ': ' + money.format(value));
    if (input.has('gas')) details.push('Газ: стоимость уточняется');
    projectDescription = [summary.textContent, ...details, 'Итого: ' + total.textContent].join('\n');
  }

  form.addEventListener('input', calculate);
  form.addEventListener('submit', event => event.preventDefault());
  request.addEventListener('submit', event => {
    if (!form.reportValidity()) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
  // Обработчик общей формы получает параметры вместе с комментарием клиента.
  request.addEventListener('formdata', event => {
    const note = event.formData.get('comment') || '';
    event.formData.set('comment', [note.trim(), projectDescription].filter(Boolean).join('\n\n'));
  });
  calculate();
})();
