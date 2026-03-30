/**
 * Finance Dashboard — app.js
 * Tab switching, signal rendering, indicator cards, Chart.js charts, theme toggle
 */

const dataCache = {};
const chartInstances = {};

/* ============ Init ============ */
document.addEventListener('DOMContentLoaded', () => {
    // Theme
    initTheme();

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const targetId = btn.getAttribute('data-target');
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');

            loadTabData(btn.getAttribute('data-source'), targetId);
        });
    });

    // Chart timeframe filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = e.target.closest('.chart-filters').getAttribute('data-target');
            
            // Update active state
            e.target.closest('.chart-filters').querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            // Re-render chart with new timeframe
            if (dataCache[targetId] && dataCache[targetId].chart) {
                renderChart(targetId, dataCache[targetId].chart);
            }
        });
    });

    loadAllPrices();
    loadNews();
    document.querySelector('.tab-btn.active').click();
});

/* ============ Theme Toggle ============ */
function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateToggleIcon(saved);

    document.getElementById('theme-toggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateToggleIcon(next);

        // Re-render active chart with new colors
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {
            const shortId = activeTab.getAttribute('data-target').replace('tab-', '');
            if (dataCache[shortId] && dataCache[shortId].chart) {
                renderChart(shortId, dataCache[shortId].chart);
            }
        }
    });
}

function updateToggleIcon(theme) {
    document.getElementById('theme-toggle').textContent = theme === 'dark' ? '☀️' : '🌙';
}

/* ============ Data Loading ============ */
async function loadAllPrices() {
    const tabs = [
        { id: 'voo', url: './data/voo.json' },
        { id: 'qqq', url: './data/qqq.json' },
        { id: '0050', url: './data/tw0050.json' },
        { id: '00713', url: './data/defense00713.json' }
    ];

    for (const tab of tabs) {
        try {
            const res = await fetch(tab.url + '?t=' + Date.now());
            if (!res.ok) continue;
            const data = await res.json();
            dataCache[tab.id] = data;

            const priceEl = document.getElementById('price-' + tab.id);
            if (priceEl && data.fund) {
                const prefix = tab.id === 'voo' ? '$' : 'NT$';
                priceEl.textContent = prefix + (data.fund.price || '--');
            }
        } catch (e) {
            console.warn('Failed to preload ' + tab.id, e);
        }
    }
}

async function loadTabData(url, tabId) {
    const shortId = tabId.replace('tab-', '');
    const gridEl = document.getElementById('grid-' + shortId);
    const fundEl = document.getElementById('fund-header-' + shortId);

    let data = dataCache[shortId];
    const loader = document.getElementById('loader');
    loader.style.display = data ? 'none' : 'flex';

    try {
        const res = await fetch(url + '?t=' + Date.now());
        if (!res.ok) throw new Error('Network error');
        data = await res.json();
        dataCache[shortId] = data;
        loader.style.display = 'none';

        document.getElementById('last-updated').textContent = '最後更新: ' + data.updated_at;

        renderFundHeader(data, fundEl, shortId);
        renderSignalBanner(data);
        renderIndicators(data.indicators, gridEl, shortId);

        // Render chart if data available
        if (data.chart && data.chart.length > 0) {
            renderChart(shortId, data.chart);
        }

    } catch (err) {
        loader.style.display = 'none';
        if (!dataCache[shortId]) {
            gridEl.innerHTML = '<div class="error-msg">無法載入數據，請稍後再試。</div>';
        }
    }
}

async function loadNews() {
    try {
        const res = await fetch('./data/news.json?t=' + Date.now());
        if (!res.ok) return;
        const data = await res.json();
        
        const tickerEl = document.getElementById('news-ticker-content');
        if (!tickerEl || !data.items || data.items.length === 0) return;
        
        // 重複項目以產生無縫滾動感
        const displayItems = [...data.items, ...data.items];

        tickerEl.innerHTML = displayItems.map(item => {
            const time = new Date(item.time).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
            return `<div class="news-item">
                <span class="news-time">[${time}]</span>
                <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
                <span style="font-size:11px;color:var(--text-muted);">— ${item.publisher}</span>
            </div>`;
        }).join('');
    } catch (e) {
        console.warn('Failed to load news', e);
    }
}

/* ============ Render Fund Header ============ */
function renderFundHeader(data, container, shortId) {
    const fund = data.fund;
    if (!fund) return;
    const prefix = shortId === 'voo' ? '$' : 'NT$';
    const changeClass = fund.change_pct >= 0 ? 'up' : 'down';
    const changeSign = fund.change_pct >= 0 ? '+' : '';

    container.innerHTML = `
        <span class="fund-price">${prefix}${fund.price}</span>
        <span class="fund-change ${changeClass}">${changeSign}${fund.change_pct}%</span>
        <span class="fund-name">${fund.name}</span>
    `;
}

/* ============ Render Signal Banner ============ */
function renderSignalBanner(data) {
    const banner = document.getElementById('signal-banner');
    const icon = document.getElementById('signal-icon');
    const title = document.getElementById('signal-title');
    const meta = document.getElementById('signal-meta');
    const reasons = document.getElementById('signal-reasons');

    banner.className = 'signal-banner';
    title.className = 'signal-title';

    // Composite signal (00713 safe haven)
    if (data.compositeSignal && data.compositeSignal.triggered) {
        banner.classList.add('safe');
        title.classList.add('safe');
        icon.textContent = '🏆';
        title.textContent = data.compositeSignal.label;
        meta.textContent = '信心指數: 99+ — 複合條件觸發';
        reasons.innerHTML = '<li>' + data.compositeSignal.description + '</li>';
        return;
    }

    const signal = data.signal;
    const map = { BUY: { icon: '📈', cls: 'buy' }, HOLD: { icon: '⏸️', cls: 'hold' }, WAIT: { icon: '⚠️', cls: 'wait' } };
    const cfg = map[signal.action] || map['HOLD'];

    banner.classList.add(cfg.cls);
    title.classList.add(cfg.cls);
    icon.textContent = cfg.icon;
    title.textContent = signal.label;
    meta.textContent = '信心指數: ' + signal.confidence + '%';
    reasons.innerHTML = signal.reasons.map(r => '<li>' + r + '</li>').join('');
}

/* ============ Render Indicator Cards ============ */
function renderIndicators(indicators, container) {
    container.innerHTML = '';

    const barConfigs = {
        fear_greed:      { min: 0, max: 100 },
        vix:             { min: 10, max: 50 },
        us_10y:          { min: 3, max: 6 },
        sp500_deviation: { min: -15, max: 15 },
        ndc_light:       { min: 9, max: 45 },
        usd_twd:         { min: 29, max: 35 },
        foreign_buy:     { min: -500, max: 500 },
        estimated_yield: { min: 0, max: 10 },
        gold:            { min: 3000, max: 6000 }
    };

    indicators.forEach(ind => {
        const card = document.createElement('div');
        card.className = 'indicator-card';

        const val = ind.value !== null && ind.value !== undefined ? ind.value : '--';
        let barHtml = '';
        const bc = barConfigs[ind.id];

        if (bc && ind.value !== null && ind.value !== undefined) {
            let pct = Math.max(0, Math.min(100, ((ind.value - bc.min) / (bc.max - bc.min)) * 100));
            let barClass = 'bar-hold';

            if (ind.id === 'fear_greed') {
                barClass = ind.value <= 25 ? 'bar-wait' : ind.value <= 50 ? 'bar-hold' : 'bar-buy';
            } else if (ind.id === 'foreign_buy') {
                barClass = ind.value > 100 ? 'bar-buy' : ind.value < -100 ? 'bar-wait' : 'bar-hold';
                pct = Math.max(0, Math.min(100, ((ind.value - (-500)) / 1000) * 100));
            } else if (ind.id === 'ndc_light') {
                barClass = ind.value <= 17 ? 'bar-buy' : ind.value >= 38 ? 'bar-wait' : 'bar-hold';
            } else if (ind.id === 'vix') {
                barClass = ind.value >= 30 ? 'bar-wait' : ind.value >= 20 ? 'bar-hold' : 'bar-buy';
            }

            barHtml = `<div class="indicator-bar"><div class="indicator-bar-fill ${barClass}" style="width:${pct}%"></div></div>`;
        }

        card.innerHTML = `
            <div class="indicator-label">${ind.name}</div>
            <div class="indicator-value-row">
                <span class="indicator-value">${val}</span>
                ${ind.unit ? '<span class="indicator-unit">' + ind.unit + '</span>' : ''}
            </div>
            ${barHtml}
        `;
        container.appendChild(card);
    });
}

/* ============ Render Price Chart ============ */
function renderChart(shortId, chartData) {
    const canvasId = 'chart-' + shortId;
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    // Get selected timeframe
    const filterContainer = document.querySelector(`.chart-filters[data-target="${shortId}"]`);
    const activeBtn = filterContainer ? filterContainer.querySelector('.filter-btn.active') : null;
    const days = activeBtn ? parseInt(activeBtn.getAttribute('data-days')) : 180;

    // Filter data to only include the last N days
    const filteredData = chartData.slice(-days);

    // Destroy previous instance
    if (chartInstances[shortId]) {
        chartInstances[shortId].destroy();
    }

    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    const lineColor = theme === 'dark' ? '#4a9eff' : '#1a73e8';
    const fillColor = theme === 'dark' ? 'rgba(74,158,255,0.08)' : 'rgba(26,115,232,0.06)';
    const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const textColor = theme === 'dark' ? '#9aa0a6' : '#5f6368';

    const labels = filteredData.map(d => d.date);
    const prices = filteredData.map(d => d.close);

    // Sample labels to avoid crowding
    const step = Math.max(1, Math.floor(labels.length / 6));

    chartInstances[shortId] = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: '收盤價',
                data: prices,
                borderColor: lineColor,
                backgroundColor: fillColor,
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHitRadius: 10,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: lineColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: theme === 'dark' ? '#22262e' : '#fff',
                    titleColor: theme === 'dark' ? '#e8eaed' : '#1a1d23',
                    bodyColor: theme === 'dark' ? '#9aa0a6' : '#5f6368',
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (item) => '收盤: ' + item.formattedValue
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: textColor,
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 7,
                        font: { size: 11 }
                    },
                    grid: { color: gridColor }
                },
                y: {
                    ticks: {
                        color: textColor,
                        font: { size: 11 }
                    },
                    grid: { color: gridColor }
                }
            }
        }
    });
}
