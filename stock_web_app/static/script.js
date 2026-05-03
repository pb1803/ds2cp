let currentOrderType = 'BUY';
let stockChart = null;
let selectedSymbol = 'TCS.NS';
let previousPrices = {}; 

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updatePrices();
    updateOrderBook();
    updateStats();
    updateTradeHistory();
    initChart();
    
    // Refresh intervals
    setInterval(updatePrices, 2000); 
    setInterval(updateChart, 2500);
    setInterval(updateOrderBook, 2000);
    setInterval(updateStats, 3000);
    setInterval(updateTradeHistory, 2000);
});

function setupEventListeners() {
    document.getElementById('orderForm').addEventListener('submit', placeOrder);
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

// --- DATA LOGIC --- //

let currentPricesData = {};

async function updatePrices() {
    try {
        const response = await fetch('/api/prices');
        const data = await response.json();

        if (data.success) {
            currentPricesData = data.prices;
            updatePricesUI();
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

function updateOrderBookTable(orders, tableId, side) {
    const tbody = document.getElementById(tableId);
    
    if (orders.length === 0) {
        tbody.innerHTML = `<tr class="empty-row"><td colspan="3">No open ${side.toLowerCase()}s</td></tr>`;
        return;
    }

    // Limit to top 15 for UI clarity
    const displayOrders = orders.slice(0, 15);

    if (side === 'BUY') {
        tbody.innerHTML = displayOrders.map(order => `
            <tr>
                <td class="font-medium">${order.symbol}</td>
                <td>${order.quantity}</td>
                <td class="text-right text-buy font-medium">₹${order.price.toFixed(2)}</td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = displayOrders.map(order => `
            <tr>
                <td class="text-sell font-medium">₹${order.price.toFixed(2)}</td>
                <td>${order.quantity}</td>
                <td class="text-right font-medium">${order.symbol}</td>
            </tr>
        `).join('');
    }
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

async function updateTradeHistory() {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();

        if (data.success && data.trades.length > 0) {
            const tbody = document.getElementById('tradesTable');
            tbody.innerHTML = data.trades.slice(0, 20).map(trade => {
                const timeStr = new Date(trade.timestamp).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'});
                const typeClass = trade.type === 'BUY' ? 'text-buy' : 'text-sell';
                
                return `
                    <tr>
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
