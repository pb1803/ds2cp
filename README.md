# ProTrade - Real-Time Stock Order Matching System 📈

ProTrade is a modern, full-stack Python trading dashboard simulation built with Flask. It realistically models a limit order book and broker-style market execution engine, complete with live dual-price mechanisms (simulating micro-fluctuations over real `yfinance` data) and a highly responsive, professional front-end layout inspired by platforms like Zerodha and TradingView.

## 🚀 Key Features

### 1. Hybrid Market Price Engine
- **Background Multi-Threaded Polling**: Fetches real market data from Yahoo Finance (`yfinance`) every 20 seconds.
- **Simulated Micro-fluctuations**: Between real data polls, applies randomized mathematical noise (±₹0.30) every 2-3 seconds to keep charts and UI feeling completely alive.
- **Fail-safe Logic**: If API endpoints hit rate limits, the system cleanly fails over to pure simulated movement without crashing.

### 2. Limit Order Matching Engine
- **Broker-style Market Execution**: Orders don't just execute blindly; they sit patiently in an active Order Book.
- The background thread dynamically checks all open limit orders against the continuous market price. Orders only execute once their limit threshold is successfully crossed.
- Supports both `BID` (BUY) and `ASK` (SELL) side queuing.

### 3. Professional Frontend (UI/UX)
- **Interactive Charting**: Implemented with **Chart.js**. The chart seamlessly updates its rendering dynamically every few seconds, adjusting to the specific stock selected. It also features dynamic trend-coloring (Green for uptrends, Red for downtrends).
- **Responsive Workspace**: Clean 2-column workspace dividing the Watchlist, Order Entry, Live Charts, Market Stats, and an expansive Market Depth (Order Book) ledger at the bottom.
- **Micro-Interactions**: Hover states, clicking a watchlist row to focus, and real-time UI data updates without refreshing the browser window.

## 🛠️ Tech Stack

- **Backend Architecture**: Python 3, Flask
- **Market Data**: `yfinance` API
- **Frontend Framework**: Vanilla HTML5, CSS3 (Modern Flexbox/Grid architecture)
- **Interactive Graphs**: Chart.js (via CDN)
- **Concurrency**: Python `threading` for background tasks and asynchronous execution.

## 📦 Project Structure

```
.
├── stock_web_app/
│   ├── app.py                      # Main Flask application and API routing
│   ├── engine/
│   │   ├── order_engine.py         # Advanced matching logic and Order Book state
│   │   └── price_manager.py        # Background thread for live yfinance data & charting history
│   ├── static/
│   │   ├── script.js               # Dynamic AJAX polling and UI interactivity logic
│   │   └── style.css               # Premium CSS design system and variables
│   └── templates/
│       └── index.html              # HTML workspace layout
└── README.md
```

## ⚙️ How to Run Locally

### Prerequisites
Make sure you have Python 3 installed. 

### 1. Clone the repository
```bash
git clone https://github.com/pb1803/ds2cp.git
cd ds2cp/stock_web_app
```

### 2. Install Dependencies
Install Flask and yfinance:
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is not available, run `pip install flask yfinance`)*

### 3. Run the application
```bash
python app.py
```

### 4. View Dashboard
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## 💡 Usage Guide

1. **Watchlist**: View the actively tracked stocks (e.g., `TCS.NS`, `RELIANCE.NS`). Click any row to automatically set the focus to that specific stock.
2. **Chart**: The interactive chart will map the history of your currently selected stock, auto-updating every 3 seconds.
3. **Place Limit Orders**: Input a specific price limit and quantity in the order form. You will see your order instantly appear in the **Market Depth** section below.
4. **Execution**: Watch the chart. As soon as the price naturally crosses your limit, your order will automatically be executed and transported to the **Trade History** log!

---
*Built as a high-fidelity system design representation of real-world stock market architectures.*
