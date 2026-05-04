let currentOrderType = 'BUY';
let stockChart = null;
let selectedSymbol = 'TCS.NS';
let previousPrices = {}; 
let socket = null;
let userPortfolio = {
    balance: 1000000, // Starting with 10L
    holdings: {}, // { "TCS.NS": { qty: 10, avgPrice: 3800 } }
    pnl: 0
};
let portfolioChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    initSocket();
    updatePrices();
    updateOrderBook();
    updateStats();
    updateTradeHistory();
    initChart();
    initPortfolio();
    initTheme();
    
    // Some things still benefit from periodic checks
    setInterval(updateStats, 5000);
    setInterval(updateIndicators, 5000);
    setInterval(updateTicker, 3000);
});

function initTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to real-time engine');
    });

    socket.on('price_update', (data) => {
        currentPricesData = data.prices;
        updatePricesUI();
        if (stockChart && data.prices[selectedSymbol]) {
            updateChart();
        }
    });

    socket.on('trade_executed', (trade) => {
        showNotification(
            `Trade Executed: ${trade.symbol}`,
            `${trade.type} ${trade.quantity} @ ₹${trade.exec_price.toFixed(2)}`,
            trade.type.toLowerCase()
        );
        
        // Simple local portfolio simulation
        const cost = trade.exec_price * trade.quantity;
        if (trade.type === 'BUY') {
            userPortfolio.balance -= cost;
            if (!userPortfolio.holdings[trade.symbol]) userPortfolio.holdings[trade.symbol] = { qty: 0, avgPrice: 0 };
            const hold = userPortfolio.holdings[trade.symbol];
            hold.avgPrice = ((hold.avgPrice * hold.qty) + cost) / (hold.qty + trade.quantity);
            hold.qty += trade.quantity;
        } else {
            userPortfolio.balance += cost;
            if (userPortfolio.holdings[trade.symbol]) {
                userPortfolio.holdings[trade.symbol].qty -= trade.quantity;
                if (userPortfolio.holdings[trade.symbol].qty <= 0) delete userPortfolio.holdings[trade.symbol];
            }
        }
        updatePortfolio();

        updateOrderBook();
        updateTradeHistory(true); 
        updateStats();
    });
}

function showNotification(title, message, type) {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    notification.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-body">${message}</div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function setupEventListeners() {
    document.getElementById('orderForm').addEventListener('submit', placeOrder);
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    
    // Search logic
    const searchInput = document.getElementById('symbolSearch');
    const searchResults = document.getElementById('searchResults');
    
    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        if (query.length < 1) {
            searchResults.style.display = 'none';
            return;
        }
        
        try {
            const res = await fetch(`/api/search?q=${query}`);
            const data = await res.json();
            if (data.success && data.results.length > 0) {
                searchResults.innerHTML = data.results.map(s => `
                    <div class="search-item" onclick="selectStock('${s}'); document.getElementById('searchResults').style.display='none'; document.getElementById('symbolSearch').value=''">
                        <strong>${s}</strong>
                    </div>
                `).join('');
                searchResults.style.display = 'block';
            } else {
                searchResults.style.display = 'none';
            }
        } catch (err) { console.error(err); }
    });
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.style.display = 'none';
        }
    });
}

// Global function exposed to HTML for row clicks
window.selectStock = function(symbol) {
    selectedSymbol = symbol;
    
    // Update UI elements
    document.getElementById('orderFormSymbolBadge').textContent = symbol;
    document.getElementById('chartTitleSymbol').textContent = symbol;
    document.getElementById('orderSymbol').value = symbol;
    
    // Update button text
    updateSubmitButton();
    
    // Refresh Chart instantly
    initChart();
    
    // Re-render prices to update selection highlighting
    updatePricesUI();
};

window.setOrderType = function(type) {
    currentOrderType = type;
    
    const buyBtn = document.querySelector('.buy-toggle');
    const sellBtn = document.querySelector('.sell-toggle');
    
    if (type === 'BUY') {
        buyBtn.classList.add('active');
        sellBtn.classList.remove('active');
    } else {
        sellBtn.classList.add('active');
        buyBtn.classList.remove('active');
    }
    
    updateSubmitButton();
};

function updateSubmitButton() {
    const btn = document.getElementById('submitOrderBtn');
    btn.textContent = `${currentOrderType} ${selectedSymbol}`;
    if (currentOrderType === 'BUY') {
        btn.className = 'btn-submit buy-action';
    } else {
        btn.className = 'btn-submit sell-action';
    }
}

function updateTicker() {
    const ticker = document.getElementById('tickerTape');
    if (!ticker || Object.keys(currentPricesData).length === 0) return;
    
    ticker.innerHTML = Object.entries(currentPricesData).map(([s, p]) => `
        <span class="ticker-item">
            ${s} <span class="ticker-price">₹${p.toFixed(2)}</span>
        </span>
    `).join(' ') + ' | ' + Object.entries(currentPricesData).map(([s, p]) => `
        <span class="ticker-item">
            ${s} <span class="ticker-price">₹${p.toFixed(2)}</span>
        </span>
    `).join(' '); // Duplicate for smooth scroll
}

function initPortfolio() {
    const ctx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Cash'],
            datasets: [{
                data: [userPortfolio.balance],
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: { legend: { display: false } }
        }
    });
    updatePortfolio();
}

function updatePortfolio() {
    let currentHoldingsValue = 0;
    const labels = ['Cash'];
    const data = [userPortfolio.balance];
    
    for (const [symbol, hold] of Object.entries(userPortfolio.holdings)) {
        const currentPrice = currentPricesData[symbol] || hold.avgPrice;
        currentHoldingsValue += hold.qty * currentPrice;
        labels.push(symbol);
        data.push(hold.qty * currentPrice);
    }
    
    const totalValue = userPortfolio.balance + currentHoldingsValue;
    const pnl = totalValue - 1000000; // vs 10L starting
    
    const pnlElement = document.getElementById('portfolioTotalPnl');
    pnlElement.textContent = `₹${pnl.toFixed(2)}`;
    pnlElement.className = pnl >= 0 ? 'pnl-value text-buy' : 'pnl-value text-sell';
    
    if (portfolioChart) {
        portfolioChart.data.labels = labels;
        portfolioChart.data.datasets[0].data = data;
        portfolioChart.update();
    }
}

// --- DATA LOGIC --- //

let currentPricesData = {};

async function updatePrices() {
    try {
        const response = await fetch('/api/prices');
        const data = await response.json();

        if (data.success) {
            currentPricesData = data.prices;
            updatePricesUI();
            updatePortfolio();
        }
    } catch (error) {
        console.error('Prices fetch error:', error);
    }
}

function updatePricesUI() {
    const tbody = document.getElementById('pricesTable');
    if (!tbody || Object.keys(currentPricesData).length === 0) return;
    
    let html = '';
    for (const [symbol, price] of Object.entries(currentPricesData)) {
        const isSelected = symbol === selectedSymbol;
        
        let trendHtml = '-';
        let trendClass = '';
        
        if (previousPrices[symbol]) {
            if (price > previousPrices[symbol]) {
                trendHtml = '↑';
                trendClass = 'text-buy';
            } else if (price < previousPrices[symbol]) {
                trendHtml = '↓';
                trendClass = 'text-sell';
            }
        }
        
        html += `
            <tr class="${isSelected ? 'selected-row' : ''}" onclick="selectStock('${symbol}')">
                <td class="font-medium">${symbol}</td>
                <td class="text-right">₹${price.toFixed(2)}</td>
                <td class="text-right ${trendClass} font-medium">${trendHtml}</td>
            </tr>
        `;
        
        previousPrices[symbol] = price;
    }
    tbody.innerHTML = html;
}

// --- CHART LOGIC --- //

async function initChart() {
    try {
        const response = await fetch(`/api/history/${selectedSymbol}`);
        const data = await response.json();
        
        if (data.success) {
            renderChart(selectedSymbol, data.timestamps, data.prices);
        }
    } catch(e) {
        console.error('Chart init error:', e);
    }
}

async function updateChart() {
    try {
        const response = await fetch(`/api/history/${selectedSymbol}`);
        const data = await response.json();
        
        if (data.success && stockChart) {
            stockChart.data.labels = data.timestamps;
            stockChart.data.datasets[0].data = data.prices;
            
            // Dynamic Mini Trend Color
            const prices = data.prices;
            if (prices.length >= 2) {
                const first = prices[0];
                const last = prices[prices.length - 1];
                const isUp = last >= first;
                
                const color = isUp ? '#16a34a' : '#dc2626'; 
                
                const ctx = document.getElementById('stockChart').getContext('2d');
                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                if (isUp) {
                    gradient.addColorStop(0, 'rgba(22, 163, 74, 0.2)');
                    gradient.addColorStop(1, 'rgba(22, 163, 74, 0)');
                } else {
                    gradient.addColorStop(0, 'rgba(220, 38, 38, 0.2)');
                    gradient.addColorStop(1, 'rgba(220, 38, 38, 0)');
                }
                
                stockChart.data.datasets[0].borderColor = color;
                stockChart.data.datasets[0].backgroundColor = gradient;
            }
            
            stockChart.update('none'); 
        }
    } catch(e) {
        console.error('Chart update error:', e);
    }
}

function renderChart(symbol, timestamps, prices) {
    const ctx = document.getElementById('stockChart').getContext('2d');
    
    if (stockChart) {
        stockChart.destroy();
    }
    
    const isUp = prices.length >= 2 ? (prices[prices.length-1] >= prices[0]) : true;
    const color = isUp ? '#16a34a' : '#dc2626';
    
    // Create Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    if (isUp) {
        gradient.addColorStop(0, 'rgba(22, 163, 74, 0.2)');
        gradient.addColorStop(1, 'rgba(22, 163, 74, 0)');
    } else {
        gradient.addColorStop(0, 'rgba(220, 38, 38, 0.2)');
        gradient.addColorStop(1, 'rgba(220, 38, 38, 0)');
    }

    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [{
                label: `Price`,
                data: prices,
                borderColor: color,
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0, 
                pointHoverRadius: 4,
                tension: 0.4, 
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            interaction: {
                intersect: false,
                mode: 'index',
            },
            layout: {
                padding: { top: 10, right: 10, bottom: 0, left: 0 }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { 
                        maxTicksLimit: 6, 
                        maxRotation: 0, 
                        color: '#9ca3af',
                        font: { size: 10 }
                    }
                },
                y: {
                    position: 'right',
                    grid: { 
                        color: 'rgba(243, 244, 246, 0.6)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#6b7280',
                        font: { size: 11, family: 'Inter' },
                        callback: function(value) { 
                            return '₹' + value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); 
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    backgroundColor: 'rgba(31, 41, 55, 0.95)',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: 'Inter', size: 12 },
                    bodyFont: { family: 'Inter', size: 14, weight: 'bold' },
                    callbacks: {
                        label: function(context) { 
                            return 'Price: ₹' + context.parsed.y.toFixed(2); 
                        }
                    }
                },
                legend: { display: false }
            }
        }
    });
}

// --- ORDER LOGIC --- //

async function placeOrder(e) {
    e.preventDefault();

    const symbol = document.getElementById('orderSymbol').value;
    const price = parseFloat(document.getElementById('orderPrice').value);
    const quantity = parseInt(document.getElementById('orderQuantity').value);

    if (!price || price <= 0 || !quantity || quantity <= 0) {
        showMessage('orderMessage', 'Invalid price or quantity', 'error');
        return;
    }

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                type: currentOrderType,
                price: price,
                quantity: quantity
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage('orderMessage', `Order placed successfully!`, 'success');
            document.getElementById('orderQuantity').value = '';
            await updateOrderBook();
            await updateStats();
            await updateTradeHistory();
        } else {
            showMessage('orderMessage', data.message, 'error');
        }
    } catch (error) {
        console.error('Order placement error:', error);
        showMessage('orderMessage', 'Error placing order', 'error');
    }
}

async function updateOrderBook() {
    try {
        const response = await fetch('/api/orderbook');
        const data = await response.json();

        if (data.success) {
            updateOrderBookTable(data.buy_side, 'buyOrdersTable', 'BUY');
            updateOrderBookTable(data.sell_side, 'sellOrdersTable', 'SELL');
        }
    } catch (error) {
        console.error('Order book update error:', error);
    }
}

socket.on('trade_executed', (trade) => {
    showNotification(
        `Trade Executed: ${trade.symbol}`,
        `${trade.type} ${trade.quantity} @ ₹${trade.exec_price.toFixed(2)}`,
        trade.type.toLowerCase()
    );
    
    // Simple local portfolio simulation
    const cost = trade.exec_price * trade.quantity;
    if (trade.type === 'BUY') {
        userPortfolio.balance -= cost;
        if (!userPortfolio.holdings[trade.symbol]) userPortfolio.holdings[trade.symbol] = { qty: 0, avgPrice: 0 };
        const hold = userPortfolio.holdings[trade.symbol];
        hold.avgPrice = ((hold.avgPrice * hold.qty) + cost) / (hold.qty + trade.quantity);
        hold.qty += trade.quantity;
    } else {
        userPortfolio.balance += cost;
        if (userPortfolio.holdings[trade.symbol]) {
            userPortfolio.holdings[trade.symbol].qty -= trade.quantity;
            if (userPortfolio.holdings[trade.symbol].qty <= 0) delete userPortfolio.holdings[trade.symbol];
        }
    }
    updatePortfolio();

    updateOrderBook();
    updateTradeHistory(true); // Pass true to trigger pulse
    updateStats();
});

function showNotification(title, message, type) {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    notification.innerHTML = `
        <div class="notification-title">${title}</div>
        <div class="notification-body">${message}</div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function setupEventListeners() {
    document.getElementById('orderForm').addEventListener('submit', placeOrder);
    
    // Search logic
    const searchInput = document.getElementById('symbolSearch');
    const searchResults = document.getElementById('searchResults');
    
    searchInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        if (query.length < 1) {
            searchResults.style.display = 'none';
            return;
        }
        
        try {
            const res = await fetch(`/api/search?q=${query}`);
            const data = await res.json();
            if (data.success && data.results.length > 0) {
                searchResults.innerHTML = data.results.map(s => `
                    <div class="search-item" onclick="selectStock('${s}'); document.getElementById('searchResults').style.display='none'; document.getElementById('symbolSearch').value=''">
                        <strong>${s}</strong>
                    </div>
                `).join('');
                searchResults.style.display = 'block';
            } else {
                searchResults.style.display = 'none';
            }
        } catch (err) { console.error(err); }
    });
    
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.style.display = 'none';
        }
    });

    document.getElementById('themeToggle').addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    });
}

function updateOrderBookTable(orders, tableId, side) {
    const tbody = document.getElementById(tableId);
    
    if (orders.length === 0) {
        tbody.innerHTML = `<tr class="empty-row"><td colspan="3">No open ${side.toLowerCase()}s</td></tr>`;
        return;
    }

    const maxVol = Math.max(...orders.map(o => o.quantity));
    const displayOrders = orders.slice(0, 15);

    let html = '';
    
    // Header row for the specific side
    html += `<tr class="side-header"><td colspan="3">${side} ORDERS</td></tr>`;

    if (side === 'BUY') {
        html += displayOrders.map(order => {
            const depthWidth = (order.quantity / maxVol) * 100;
            return `
                <tr class="depth-row">
                    <td class="font-medium">${order.symbol}</td>
                    <td>${order.quantity}</td>
                    <td class="text-right text-buy font-medium">₹${order.price.toFixed(2)}</td>
                    <div class="depth-bar" style="width: ${depthWidth}%"></div>
                </tr>
            `;
        }).join('');
    } else {
        html += displayOrders.map(order => {
            const depthWidth = (order.quantity / maxVol) * 100;
            return `
                <tr class="depth-row">
                    <td class="text-sell font-medium">₹${order.price.toFixed(2)}</td>
                    <td>${order.quantity}</td>
                    <td class="text-right font-medium">${order.symbol}</td>
                    <div class="depth-bar" style="width: ${depthWidth}%"></div>
                </tr>
            `;
        }).join('');
    }
    
    tbody.innerHTML = html;
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            document.getElementById('statBuyOrders').textContent = stats.total_buy_orders;
            document.getElementById('statSellOrders').textContent = stats.total_sell_orders;
            document.getElementById('statTrades').textContent = stats.trades_executed;
            document.getElementById('statVolume').textContent = stats.total_volume;
        }
    } catch (error) {
        console.error('Stats update error:', error);
    }
}

async function updateTradeHistory(shouldPulse = false) {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();

        if (data.success && data.trades.length > 0) {
            const tbody = document.getElementById('tradesTable');
            tbody.innerHTML = data.trades.slice(0, 20).map((trade, index) => {
                const timeStr = new Date(trade.timestamp).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'});
                const typeClass = trade.type === 'BUY' ? 'text-buy' : 'text-sell';
                const pulseClass = (shouldPulse && index === 0) ? 'new-trade-row' : '';
                
                return `
                    <tr class="${pulseClass}">
                        <td class="text-xs text-gray">${timeStr}</td>
                        <td class="font-medium">${trade.symbol}</td>
                        <td class="${typeClass} font-medium">${trade.type}</td>
                        <td class="text-right">₹${trade.order_price.toFixed(2)}</td>
                        <td class="text-right font-medium">₹${trade.market_price.toFixed(2)}</td>
                        <td class="text-right">${trade.quantity}</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (error) {
        console.error('Trade history update error:', error);
    }
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `message-box ${type}`;
    element.style.display = 'block';
    
    if (type === 'success') {
        setTimeout(() => { 
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.display = 'none';
                element.style.opacity = '1';
                element.textContent = '';
            }, 300);
        }, 3000);
    }
}

async function updateIndicators() {
    try {
        const response = await fetch(`/api/indicators/${selectedSymbol}`);
        const data = await response.json();
        
        if (data.success && data.indicators.status === "success") {
            const ind = data.indicators;
            const titleElement = document.getElementById('chartTitleSymbol');
            
            // Format labels
            const smaText = ind.sma > 0 ? ` | SMA: ₹${ind.sma.toFixed(2)}` : '';
            const rsiText = ind.rsi > 0 ? ` | RSI: ${ind.rsi.toFixed(0)}` : '';
            
            titleElement.innerHTML = `${selectedSymbol} <small style="font-size: 0.8rem; color: var(--text-muted); font-weight: 400;">${smaText}${rsiText}</small>`;
        }
    } catch (e) {
        console.error('Indicators fetch error:', e);
    }
}
