/* JFD Hospital HMS — Chart.js Helper Module */
const JFDCharts = {
  instances: {},
  colors: {
    blue:    { bg: 'rgba(59,130,246,0.12)', border: '#3b82f6' },
    emerald: { bg: 'rgba(16,185,129,0.12)', border: '#10b981' },
    amber:   { bg: 'rgba(245,158,11,0.12)', border: '#f59e0b' },
    rose:    { bg: 'rgba(244,63,94,0.12)',  border: '#f43f5e' },
    violet:  { bg: 'rgba(139,92,246,0.12)', border: '#8b5cf6' },
    navy:    { bg: 'rgba(15,23,42,0.08)',   border: '#0f172a' },
    slate:   { bg: 'rgba(100,116,139,0.12)',border: '#64748b' },
  },
  defaults: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        titleColor: '#fff',
        bodyColor: '#e2e8f0',
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 1,
        cornerRadius: 10,
        padding: 12,
        boxPadding: 4,
        usePointStyle: true,
        titleFont: { family: 'Inter', weight: '600', size: 13 },
        bodyFont: { family: 'Inter', size: 12 },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 11 } } },
      y: { grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { family: 'Inter', size: 11 } } },
    },
  },

  init(canvasId, type, data, opts = {}) {
    if (this.instances[canvasId]) {
      this.instances[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const config = {
      type,
      data,
      options: { ...this.defaults, ...opts },
    };
    if (type === 'doughnut' || type === 'pie') {
      delete config.options.scales;
      config.options.cutout = opts.cutout || '72%';
      config.options.plugins.legend = opts.legend || { display: false };
    }
    this.instances[canvasId] = new Chart(ctx, config);
    return this.instances[canvasId];
  },

  bar(canvasId, labels, datasets, opts = {}) {
    const ds = datasets.map((d, i) => ({
      label: d.label || '',
      data: d.data,
      backgroundColor: d.color ? this.colors[d.color]?.border : Object.values(this.colors)[i]?.border,
      borderRadius: 6,
      borderSkipped: false,
      maxBarThickness: 36,
      ...d,
    }));
    return this.init(canvasId, 'bar', { labels, datasets: ds }, opts);
  },

  line(canvasId, labels, datasets, opts = {}) {
    const ds = datasets.map((d, i) => {
      const c = d.color ? this.colors[d.color] : Object.values(this.colors)[i];
      return {
        label: d.label || '',
        data: d.data,
        borderColor: c.border,
        backgroundColor: c.bg,
        fill: true,
        tension: 0.4,
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: c.border,
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2,
        ...d,
      };
    });
    return this.init(canvasId, 'line', { labels, datasets: ds }, opts);
  },

  doughnut(canvasId, labels, data, colors, opts = {}) {
    const bgColors = colors.map(c => this.colors[c]?.border || c);
    const hoverColors = bgColors.map(c => c + 'dd');
    return this.init(canvasId, 'doughnut', {
      labels,
      datasets: [{ data, backgroundColor: bgColors, hoverBackgroundColor: hoverColors, borderWidth: 0, borderRadius: 4, spacing: 2 }],
    }, { cutout: '72%', ...opts });
  },

  destroy(canvasId) {
    if (this.instances[canvasId]) {
      this.instances[canvasId].destroy();
      delete this.instances[canvasId];
    }
  },

  destroyAll() {
    Object.keys(this.instances).forEach(id => this.destroy(id));
  },
};
