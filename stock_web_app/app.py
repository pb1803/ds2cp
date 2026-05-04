from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import subprocess
import os
import threading
import time
from datetime import datetime

class CPPEngineWrapper:
    def __init__(self):
        self.engine_path = os.path.join(os.path.dirname(__file__), "engine_cpp", "engine.exe")
        self.process = subprocess.Popen(
            [self.engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.lock = threading.Lock()
        self.metrics = {
            "insert_times": [], # in milliseconds
            "match_times": [],  # in milliseconds
            "total_orders": 0,
            "total_matches": 0
        }

    def _send_command(self, cmd):
        with self.lock:
            self.process.stdin.write(json.dumps(cmd) + "\n")
            line = self.process.stdout.readline()
            if not line:
                return {"status": "error", "message": "Engine crashed"}
            return json.loads(line)

    def place_order(self, symbol, order_type, price, quantity):
        cmd = {
            "action": "place_order",
            "symbol": symbol,
            "type": order_type,
            "price": price,
            "quantity": quantity
        }
        res = self._send_command(cmd)
        if res.get("status") == "success":
            # Record metrics (convert microseconds to milliseconds)
            self.metrics["insert_times"].append(res.get("exec_time_us", 0) / 1000.0)
            self.metrics["total_orders"] += 1
            return {
                "success": True, 
                "message": f"Order {res['order_id']} placed in C++ AVL Tree.",
                "order_id": res["order_id"]
            }
        return {"success": False, "message": "C++ Engine Error"}

    def process_market_orders(self, prices):
        cmd = {"action": "process_market_orders"}
        cmd.update(prices)
        res = self._send_command(cmd)
        if res.get("status") == "success":
            self.metrics["match_times"].append(res.get("exec_time_us", 0) / 1000.0)
            self.metrics["total_matches"] += res.get("executed_count", 0)
        return res

    def get_order_book(self):
        res = self._send_command({"action": "get_order_book"})
        return {
            "buy_side": res.get("buy_side", []),
            "sell_side": res.get("sell_side", [])
        }

    def get_trade_history(self, start=None, end=None):
        cmd = {"action": "get_trades"}
        if start and end:
            cmd["start"] = start
            cmd["end"] = end
        res = self._send_command(cmd)
        return res.get("trades", [])

    def get_stats(self):
        res = self._send_command({"action": "get_stats"})
        return res.get("stats", {})

    def get_indicators(self, symbol):
        res = self._send_command({"action": "get_indicators", "symbol": symbol})
        return res

    def search_symbols(self, query):
        res = self._send_command({"action": "search_symbols", "query": query})
        return res.get("results", [])

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize C++ engine wrapper
engine = CPPEngineWrapper()

from engine.price_manager import PriceManager

def on_price_update(prices):
    """Callback function triggered by PriceManager when prices change"""
    res = engine.process_market_orders(prices)
    
    # Broadcast new prices
    socketio.emit('price_update', {"prices": prices, "timestamp": datetime.now().isoformat()})
    
    # Check for executed trades and notify
    if res.get("status") == "success" and res.get("executed_count", 0) > 0:
        for trade in res.get("trades", []):
            socketio.emit('trade_executed', trade)
            
# Initialize and start the background price manager
price_manager = PriceManager(on_price_update=on_price_update)
price_manager.start()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/performance-page')
def performance_page():
    """Serve the performance metrics page"""
    return render_template('performance.html')

@app.route('/api/performance')
def get_performance():
    """Return engine performance metrics"""
    m = engine.metrics
    avg_insert = sum(m["insert_times"]) / len(m["insert_times"]) if m["insert_times"] else 0
    avg_match = sum(m["match_times"]) / len(m["match_times"]) if m["match_times"] else 0
    
    return jsonify({
        "success": True,
        "avg_insert_time": avg_insert,
        "avg_match_time": avg_match,
        "total_orders": m["total_orders"],
        "total_matches": m["total_matches"],
        "insert_history": m["insert_times"][-20:], # Last 20 ops
        "match_history": m["match_times"][-20:]
    })

@app.route('/api/history/<symbol>', methods=['GET'])
def get_history(symbol):
    """Fetch price history for chart"""
    try:
        history = price_manager.get_history(symbol)
        return jsonify({
            "success": True,
            "symbol": symbol,
            "timestamps": history["timestamps"],
            "prices": history["prices"]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/history/range', methods=['POST'])
def get_trade_range():
    """Fetch trade history in a specific date/time range using C++ B+ Tree"""
    try:
        data = request.json
        start = data.get("start")
        end = data.get("end")
        trades = engine.get_trade_history(start, end)
        return jsonify({"success": True, "trades": trades})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/indicators/<symbol>', methods=['GET'])
def get_indicators(symbol):
    """Fetch SMA/RSI calculated in C++ engine"""
    try:
        res = engine.get_indicators(symbol)
        return jsonify({"success": True, "symbol": symbol, "indicators": res})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/prices', methods=['GET'])
def get_all_prices():
    """Fetch live prices for all stocks"""
    try:
        prices = price_manager.get_prices()
        return jsonify({
            "success": True,
            "prices": prices,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/order', methods=['POST'])
def place_order():
    """Submit a new order to the C++ Engine"""
    try:
        data = request.json
        res = engine.place_order(
            data['symbol'], 
            data['type'], 
            float(data['price']), 
            int(data['quantity'])
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/orderbook', methods=['GET'])
def get_book():
    """Get full order book from C++ AVL Trees"""
    try:
        book = engine.get_order_book()
        return jsonify({
            "success": True,
            "buy_side": book["buy_side"],
            "sell_side": book["sell_side"]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history from C++ all_trades list"""
    try:
        trades = engine.get_trade_history()
        return jsonify({
            "success": True,
            "trades": trades,
            "count": len(trades)
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics from C++ Engine"""
    try:
        stats = engine.get_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/search', methods=['GET'])
def search():
    """Symbol search using C++ Trie"""
    query = request.args.get('q', '')
    results = engine.search_symbols(query)
    return jsonify({"success": True, "results": results})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
