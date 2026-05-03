from flask import Flask, render_template, request, jsonify
import json
import subprocess
import os
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

    def _send_command(self, cmd):
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
            return {
                "success": True, 
                "message": f"Order {res['order_id']} placed in C++ AVL Tree.",
                "order_id": res["order_id"]
            }
        return {"success": False, "message": "C++ Engine Error"}

    def process_market_orders(self, prices):
        cmd = {"action": "process_market_orders"}
        cmd.update(prices)
        return self._send_command(cmd)

    def get_order_book(self):
        res = self._send_command({"action": "get_order_book"})
        return {
            "buy_side": res.get("buy_side", []),
            "sell_side": res.get("sell_side", [])
        }

    def get_trade_history(self):
        res = self._send_command({"action": "get_trades"})
        return res.get("trades", [])

    def get_stats(self):
        res = self._send_command({"action": "get_stats"})
        return res.get("stats", {})

    def search_symbols(self, query):
        res = self._send_command({"action": "search_symbols", "query": query})
        return res.get("results", [])

app = Flask(__name__)

# Initialize C++ engine wrapper
engine = CPPEngineWrapper()

from engine.price_manager import PriceManager

def on_price_update(prices):
    """Callback function triggered by PriceManager when prices change"""
    engine.process_market_orders(prices)

# Initialize and start the background price manager
price_manager = PriceManager(on_price_update=on_price_update)
price_manager.start()

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

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
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/price/<symbol>', methods=['GET'])
def get_price(symbol):
    """Fetch live price for a specific stock symbol"""
    try:
        price = price_manager.get_price(symbol)
        if price is None:
            return jsonify({
                "success": False,
                "error": f"Symbol {symbol} not found",
                "price": None
            }), 404
            
        return jsonify({
            "success": True,
            "symbol": symbol,
            "price": float(price),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/history/<symbol>', methods=['GET'])
def get_history(symbol):
    """Fetch price history for a specific stock symbol for charting"""
    try:
        if symbol not in PriceManager.STOCKS:
            return jsonify({
                "success": False,
                "error": "Invalid symbol"
            }), 404
            
        history = price_manager.get_history(symbol)
        return jsonify({
            "success": True,
            "symbol": symbol,
            "timestamps": history["timestamps"],
            "prices": history["prices"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/order', methods=['POST'])
def place_order():
    """Place a new order into the order book"""
    try:
        data = request.get_json()
        
        # Validation
        order_type = data.get('type', '').upper()
        symbol = data.get('symbol', '').upper()
        
        if order_type not in ['BUY', 'SELL']:
            return jsonify({"success": False, "message": "Invalid order type"}), 400
            
        if not symbol or symbol not in PriceManager.STOCKS:
            return jsonify({"success": False, "message": "Invalid stock symbol"}), 400
        
        try:
            price = float(data.get('price', 0))
            quantity = int(data.get('quantity', 0))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid price or quantity"}), 400
        
        if price <= 0 or quantity <= 0:
            return jsonify({"success": False, "message": "Price and quantity must be positive"}), 400
        
        # Place order using the engine (adds to order book, waits for execution)
        result = engine.place_order(symbol, order_type, price, quantity)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/orderbook', methods=['GET'])
def get_orderbook():
    """Get current order book"""
    try:
        book = engine.get_order_book()
        return jsonify({
            "success": True,
            "buy_side": book["buy_side"],
            "sell_side": book["sell_side"],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        trades = engine.get_trade_history()
        return jsonify({
            "success": True,
            "trades": trades,
            "count": len(trades),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get engine statistics"""
    try:
        stats = engine.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/search', methods=['GET'])
def search_symbols():
    """Search stock symbols using Trie."""
    try:
        query = request.args.get('q', '')
        results = engine.search_symbols(query)
        return jsonify({
            "success": True,
            "query": query,
            "results": results
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
