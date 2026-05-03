from datetime import datetime
from typing import List, Dict
import threading
from engine.dsa.avl_tree import AVLTree
from engine.dsa.trie import Trie
from engine.dsa.depq import DEPQ
from engine.dsa.bplus_tree import BPlusTree

class OrderEngine:
    """
    Advanced Stock Order Matching Engine using DSA.
    - AVL Trees for price-sorted Order Book.
    - DEPQ for efficient Best Bid/Ask access.
    - Trie for stock symbol searching.
    - B+ Tree for trade history indexing.
    """
    
    def __init__(self, stock_symbols: List[str]):
        self.lock = threading.Lock()
        self.order_counter = 0
        self.trade_counter = 0
        
        # O(1) lookup by order_id
        self.orders_by_id = {}
        
        # AVL Trees for each stock (Price -> List of Orders)
        self.buy_trees = {symbol: AVLTree() for symbol in stock_symbols}
        self.sell_trees = {symbol: AVLTree() for symbol in stock_symbols}
        
        # DEPQ for Best Bid/Ask per stock
        self.depqs = {symbol: DEPQ() for symbol in stock_symbols}
        
        # Trie for stock symbol searching
        self.symbol_trie = Trie()
        for symbol in stock_symbols:
            self.symbol_trie.insert(symbol)
            
        # B+ Tree for Trade History indexing by timestamp
        self.trade_bplus_tree = BPlusTree(order=8)
        self.all_trades = [] # Keep list for quick reverse retrieval
    
    def place_order(self, symbol: str, order_type: str, price: float, quantity: int) -> Dict:
        """Place a new order using AVL Trees and DEPQ."""
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
            
            # 1. Store in O(1) lookup
            self.orders_by_id[order_id] = order
            
            # 2. Store in AVL Tree (Price level)
            if order_type.upper() == "BUY":
                self.buy_trees[symbol].root = self.buy_trees[symbol].insert(self.buy_trees[symbol].root, price, order)
            else:
                self.sell_trees[symbol].root = self.sell_trees[symbol].insert(self.sell_trees[symbol].root, price, order)
            
            # 3. Update DEPQ
            self.depqs[symbol].insert(price, order_id)
            
        return {
            "success": True,
            "message": f"Order {order_id} placed in Order Book using AVL Tree.",
            "order_id": order_id
        }

    def process_market_orders(self, market_prices: Dict[str, float]) -> Dict:
        """Execute orders based on market price using AVL Tree traversal."""
        executed_trades = []
        
        with self.lock:
            for symbol, m_price in market_prices.items():
                # Process BUY orders (Market Price <= Order Price)
                # We need all nodes in BUY tree with price >= m_price
                self._match_buy_orders(symbol, m_price, executed_trades)
                
                # Process SELL orders (Market Price >= Order Price)
                # We need all nodes in SELL tree with price <= m_price
                self._match_sell_orders(symbol, m_price, executed_trades)
        
        return {
            "executed_count": len(executed_trades),
            "executed_trades": executed_trades
        }

    def _match_buy_orders(self, symbol, m_price, executed_trades):
        """Find and execute BUY orders where market_price <= limit_price."""
        tree = self.buy_trees[symbol]
        # We need to find all orders with price >= m_price
        # In a sorted tree, these are the nodes from m_price up to max
        # For simplicity, we can get inorder traversal and filter, 
        # or implement a more efficient range search in AVL.
        nodes = []
        tree.inorder(tree.root, nodes)
        
        for node in nodes:
            if node.price >= m_price:
                for order in list(node.orders):
                    self._execute_order(order, m_price, executed_trades)
                    node.orders.remove(order)
                    self.depqs[symbol].remove(order["id"])
                    del self.orders_by_id[order["id"]]
                
                if not node.orders:
                    tree.root = tree.delete(tree.root, node.price)

    def _match_sell_orders(self, symbol, m_price, executed_trades):
        """Find and execute SELL orders where market_price >= limit_price."""
        tree = self.sell_trees[symbol]
        # We need to find all orders with price <= m_price
        nodes = []
        tree.inorder(tree.root, nodes)
        
        for node in nodes:
            if node.price <= m_price:
                for order in list(node.orders):
                    self._execute_order(order, m_price, executed_trades)
                    node.orders.remove(order)
                    self.depqs[symbol].remove(order["id"])
                    del self.orders_by_id[order["id"]]
                
                if not node.orders:
                    tree.root = tree.delete(tree.root, node.price)

    def _execute_order(self, order, m_price, executed_trades):
        self.trade_counter += 1
        trade = {
            "trade_id": f"TRD-{self.trade_counter}",
            "order_id": order["id"],
            "symbol": order["symbol"],
            "type": order["type"],
            "limit_price": order["price"],
            "exec_price": float(m_price),
            "order_price": order["price"], # compatibility
            "market_price": float(m_price), # compatibility
            "quantity": order["quantity"],
            "timestamp": datetime.now().isoformat()
        }
        self.all_trades.append(trade)
        # Index in B+ Tree by timestamp (string)
        self.trade_bplus_tree.insert(trade["timestamp"], trade)
        executed_trades.append(trade)

    def get_order_book(self) -> Dict:
        """Get order book by traversing AVL Trees."""
        buy_side = []
        sell_side = []
        
        with self.lock:
            for symbol in self.buy_trees:
                # Traverse BUY AVL Tree
                nodes = []
                self.buy_trees[symbol].inorder(self.buy_trees[symbol].root, nodes)
                for node in nodes:
                    for order in node.orders:
                        buy_side.append({
                            "symbol": order["symbol"],
                            "price": order["price"],
                            "quantity": order["quantity"],
                            "id": order["id"]
                        })
                
                # Traverse SELL AVL Tree
                nodes = []
                self.sell_trees[symbol].inorder(self.sell_trees[symbol].root, nodes)
                for node in nodes:
                    for order in node.orders:
                        sell_side.append({
                            "symbol": order["symbol"],
                            "price": order["price"],
                            "quantity": order["quantity"],
                            "id": order["id"]
                        })
        
        # Sort for display (AVL inorder is sorted)
        buy_side.sort(key=lambda x: x["price"], reverse=True)
        sell_side.sort(key=lambda x: x["price"])
        
        return {
            "buy_side": buy_side,
            "sell_side": sell_side
        }

    def search_symbols(self, prefix: str) -> List[str]:
        """Use Trie for symbol prefix search."""
        return self.symbol_trie.search(prefix.upper())

    def get_trade_history(self, start_time: str = None, end_time: str = None) -> List[Dict]:
        """Get trade history, using B+ Tree for range queries if times provided."""
        if start_time and end_time:
            return self.trade_bplus_tree.get_range(start_time, end_time)
        return sorted(self.all_trades, key=lambda x: x["timestamp"], reverse=True)

    def get_stats(self) -> Dict:
        """Get engine statistics using AVL/Dict data."""
        with self.lock:
            total_buy_orders = sum(1 for o in self.orders_by_id.values() if o["type"] == "BUY")
            total_sell_orders = sum(1 for o in self.orders_by_id.values() if o["type"] == "SELL")
            total_buy_qty = sum(o["quantity"] for o in self.orders_by_id.values() if o["type"] == "BUY")
            total_sell_qty = sum(o["quantity"] for o in self.orders_by_id.values() if o["type"] == "SELL")
            
            return {
                "total_buy_orders": total_buy_orders,
                "total_sell_orders": total_sell_orders,
                "total_buy_quantity": int(total_buy_qty),
                "total_sell_quantity": int(total_sell_qty),
                "trades_executed": len(self.all_trades),
                "total_volume": sum(t["quantity"] for t in self.all_trades)
            }

    def get_best_prices(self, symbol: str) -> Dict:
        """Access best prices using DEPQ in O(1) for top element."""
        return {
            "best_bid": self.depqs[symbol].get_max(),
            "best_ask": self.depqs[symbol].get_min()
        }
