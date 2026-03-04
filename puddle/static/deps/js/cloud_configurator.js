(function () {
  const planGrid = document.getElementById('plan-grid');
  if (!planGrid) {
    return;
  }

  const cpuInput = document.getElementById('cpu-input');
  const ramInput = document.getElementById('ram-input');
  const diskInput = document.getElementById('disk-input');
  const cpuValue = document.getElementById('cpu-value');
  const ramValue = document.getElementById('ram-value');
  const diskValue = document.getElementById('disk-value');
  const summaryPrice = document.getElementById('summary-price');
  const summaryDesc = document.getElementById('summary-desc');
  const summaryResources = document.getElementById('summary-resources');
  const advisorBox = document.getElementById('advisor-box');
  const cpuGroup = document.getElementById('cpu-group');

  const periods = {
    day: {label: 'BYN/день', factor: 1},
    month: {label: 'BYN/мес', factor: 30},
    year: {label: 'BYN/год', factor: 30 * 12 * 0.8},
  };

  let activeOS = 'Ubuntu 22.04';
  let activePlan = planGrid.querySelector('.plan-card.active');
  let activePeriod = 'month';
  let currentPrice = 0;

  function toNumber(value) {
    return Number.parseFloat(value || 0);
  }

  function applyPlan(planEl) {
    if (!planEl) {
      return;
    }

    planGrid.querySelectorAll('.plan-card').forEach((card) => card.classList.remove('active'));
    planEl.classList.add('active');
    activePlan = planEl;

    cpuInput.value = planEl.dataset.cpu;
    ramInput.value = planEl.dataset.ram;
    diskInput.value = planEl.dataset.disk;

    activeOS = planEl.dataset.os;
    document.querySelectorAll('.os-item').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.os === activeOS);
    });

    recalc();
  }

  function getAddonPrice() {
    let addons = 0;
    if (document.getElementById('opt-ip').checked) {
      addons += 0.4;
    }
    if (document.getElementById('opt-backup').checked) {
      addons += 0.9;
    }
    if (document.getElementById('opt-ddos').checked) {
      addons += 1.3;
    }
    if (activeOS === 'Windows Server') {
      addons += 1.5;
    }
    return addons;
  }

  function animatePrice(target) {
    const start = currentPrice;
    const duration = 260;
    const startTime = performance.now();

    function step(time) {
      const progress = Math.min((time - startTime) / duration, 1);
      const value = start + (target - start) * progress;
      const period = periods[activePeriod];
      summaryPrice.textContent = `${value.toFixed(2)} ${period.label}`;
      if (progress < 1) {
        requestAnimationFrame(step);
      }
    }

    currentPrice = target;
    requestAnimationFrame(step);
  }

  function recalc() {
    const cpu = toNumber(cpuInput.value);
    const ram = toNumber(ramInput.value);
    const disk = toNumber(diskInput.value);

    cpuValue.textContent = cpu;
    ramValue.textContent = ram;
    diskValue.textContent = disk;

    const base = toNumber(activePlan.dataset.price);
    const dynamic = cpu * 0.5 + ram * 0.18 + disk * 0.02 + getAddonPrice();
    const dayPrice = base + dynamic;
    const total = dayPrice * periods[activePeriod].factor;

    summaryDesc.textContent = `Вы выбрали: ${activeOS} + ${activePlan.dataset.name}`;
    summaryResources.textContent = `${cpu} vCPU / ${ram} GB RAM / ${disk} GB NVMe`;

    const needsAdvisor = ram >= 128 && cpu <= 8;
    advisorBox.style.display = needsAdvisor ? 'block' : 'none';
    cpuGroup.classList.toggle('range-warning', needsAdvisor);

    animatePrice(total);
  }

  planGrid.querySelectorAll('.plan-card').forEach((card) => {
    card.addEventListener('click', () => applyPlan(card));
  });

  document.querySelectorAll('.os-item').forEach((item) => {
    item.addEventListener('click', () => {
      activeOS = item.dataset.os;
      document.querySelectorAll('.os-item').forEach((btn) => btn.classList.remove('active'));
      item.classList.add('active');
      recalc();
    });
  });

  document.querySelectorAll('.period-btn').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.period-btn').forEach((btn) => btn.classList.remove('active'));
      button.classList.add('active');
      activePeriod = button.dataset.period;
      recalc();
    });
  });

  [cpuInput, ramInput, diskInput, document.getElementById('opt-ip'), document.getElementById('opt-backup'), document.getElementById('opt-ddos')]
    .forEach((el) => el.addEventListener('input', recalc));

  applyPlan(activePlan);
})();
