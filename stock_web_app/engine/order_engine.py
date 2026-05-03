from datetime import datetime
from typing import List, Dict
import threading

class OrderEngine:
    """
    Stock Order Matching Engine updated for Hybrid execution.
    Matches directly against the live market price instead of matching users with users.
    Orders wait in the order book until market price reaches their limit price.
    """
    
    def __init__(self):
        self.order_book = {}  # {order_id: order}
        self.trade_history = []  # List of executed trades
        self.order_counter = 0  # Auto-incrementing order IDs
        self.trade_counter = 0  # Auto-incrementing trade IDs
        self.lock = threading.Lock()
    
    def place_order(self, symbol: str, order_type: str, price: float, quantity: int) -> Dict:
        """Place a new order (BUY or SELL). Order goes into the book to wait for market execution."""
        if quantity <= 0 or price <= 0:
            return {"success": False, "message": "Invalid price or quantity"}
        
        with self.lock:
            self.order_counter += 1
            order_id = f"ORD-{self.order_counter}"
            
            order = {
                "id": order_id,
                "symbol": symbol,
                "type": order_type.upper(),
                "price": float(price),
                "quantity": int(quantity),
                "original_quantity": int(quantity),
                "timestamp": datetime.now().isoformat()
            }
            
            self.order_book[order_id] = order
            
        return {
            "success": True,
            "message": f"Order {order_id} placed in Order Book. Waiting for limit price.",
            "order_id": order_id
        }

    def process_market_orders(self, market_prices: Dict[str, float]) -> Dict:
        """
        Execute orders based on current market prices.
        Called periodically by the background PriceManager.
        """
        executed = []
        
        with self.lock:
            # Iterate over a list to allow safe deletion from dict
            for order_id, order in list(self.order_book.items()):
                symbol = order["symbol"]
                m_price = market_prices.get(symbol)
                if not m_price:
                    continue
                    
                # BUY condition: market price drops to or below limit price
                if order["type"] == "BUY" and m_price <= order["price"]:
                    self.trade_counter += 1
                    trade = {
                        "trade_id": f"TRD-{self.trade_counter}",
                        "order_id": order_id,
                        "symbol": symbol,
                        "type": "BUY",
                        "limit_price": order["price"],
                        "exec_price": float(m_price),
                        "order_price": order["price"], # Used for backwards compatibility with UI
                        "market_price": float(m_price), # Used for backwards compatibility with UI
                        "quantity": order["quantity"],
                        "timestamp": datetime.now().isoformat()
                    }
                    self.trade_history.append(trade)
                    executed.append(trade)
                    
                    # Fully executed, remove from book
                    del self.order_book[order_id]
                    
                # SELL condition: market price rises to or above limit price
                elif order["type"] == "SELL" and m_price >= order["price"]:
                    self.trade_counter += 1
                    trade = {
                        "trade_id": f"TRD-{self.trade_counter}",
                        "order_id": order_id,
                        "symbol": symbol,
                        "type": "SELL",
                        "limit_price": order["price"],
                        "exec_price": float(m_price),
                        "order_price": order["price"], # Used for backwards compatibility with UI
                        "market_price": float(m_price), # Used for backwards compatibility with UI
                        "quantity": order["quantity"],
                        "timestamp": datetime.now().isoformat()
                    }
                    self.trade_history.append(trade)
                    executed.append(trade)
                    
                    # Fully executed, remove from book
                    del self.order_book[order_id]
            
        return {
            "executed_count": len(executed),
            "executed_trades": executed
        }
    
    def get_order_book(self) -> Dict:
        """Get current state of buy and sell orders"""
        buy_side = []
        sell_side = []
        
        with self.lock:
            for order in self.order_book.values():
                entry = {
                    "symbol": order["symbol"],
                    "price": order["price"],
                    "quantity": order["quantity"],
                    "id": order["id"]
                }
                if order["type"] == "BUY":
                    buy_side.append(entry)
                else:
                    sell_side.append(entry)
            
        # Sort for display
        buy_side.sort(key=lambda x: x["price"], reverse=True)  # Highest first
        sell_side.sort(key=lambda x: x["price"])  # Lowest first
        
        return {
            "buy_side": buy_side,
            "sell_side": sell_side
        }
    
    def get_trade_history(self) -> List[Dict]:
        """Get all executed trades"""
        with self.lock:
            return sorted(self.trade_history, key=lambda x: x["timestamp"], reverse=True)
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        with self.lock:
            total_buy_quantity = sum(o["quantity"] for o in self.order_book.values() if o["type"] == "BUY")
            total_sell_quantity = sum(o["quantity"] for o in self.order_book.values() if o["type"] == "SELL")
            
            return {
                "total_buy_orders": sum(1 for o in self.order_book.values() if o["type"] == "BUY"),
                "total_sell_orders": sum(1 for o in self.order_book.values() if o["type"] == "SELL"),
                "total_buy_quantity": int(total_buy_quantity),
                "total_sell_quantity": int(total_sell_quantity),
                "trades_executed": len(self.trade_history),
                "total_volume": sum(t["quantity"] for t in self.trade_history)
            }
