import yfinance as yf
import threading
import time
import random
from datetime import datetime
from typing import Dict, Callable

class PriceManager:
    """
    Hybrid Real + Simulated Price Engine with History Tracking
    """
    
    STOCKS = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]
    HISTORY_LIMIT = 200
    
    def __init__(self, on_price_update: Callable[[Dict[str, float]], None] = None):
        # Default starting prices
        self.prices = {
            "TCS.NS": 3800.0,
            "INFY.NS": 1600.0,
            "RELIANCE.NS": 2900.0,
            "HDFCBANK.NS": 1400.0,
            "ICICIBANK.NS": 1000.0,
            "SBIN.NS": 750.0
        }
        
        self.price_history = {symbol: [] for symbol in self.STOCKS}
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.on_price_update = on_price_update
        
        # Initialize history with starting prices
        now = datetime.now().strftime("%H:%M:%S")
        for symbol in self.STOCKS:
            self.price_history[symbol].append((now, self.prices[symbol]))
            
    def start(self):
        """Start the background thread for price updates"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the background thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
    def get_prices(self) -> Dict[str, float]:
        """Return all current prices"""
        with self.lock:
            return self.prices.copy()
            
    def get_price(self, symbol: str) -> float:
        """Return price for a specific symbol"""
        with self.lock:
            return self.prices.get(symbol)
            
    def get_history(self, symbol: str) -> Dict:
        """Return price history for a specific symbol"""
        with self.lock:
            history = self.price_history.get(symbol, [])
            return {
                "timestamps": [t for t, p in history],
                "prices": [p for t, p in history]
            }
            
    def _add_history(self, symbol: str, price: float):
        """Add price to history and maintain limit"""
        now = datetime.now().strftime("%H:%M:%S")
        history = self.price_history[symbol]
        
        # If the last timestamp is the exact same second, update it rather than appending
        # This prevents chart stuttering if multiple updates happen in 1 second
        if history and history[-1][0] == now:
            history[-1] = (now, price)
        else:
            history.append((now, price))
            
        if len(history) > self.HISTORY_LIMIT:
            history.pop(0)

    def _fetch_real_prices(self):
        """Fetch actual prices from yfinance"""
        try:
            tickers = yf.Tickers(" ".join(self.STOCKS))
            updated = False
            for symbol in self.STOCKS:
                try:
                    data = tickers.tickers[symbol].history(period='1d')
                    if not data.empty:
                        price = float(data['Close'].iloc[-1])
                        with self.lock:
                            self.prices[symbol] = price
                            self._add_history(symbol, price)
                        updated = True
                except Exception:
                    pass  # Ignore if a single stock fetch fails
            
            if updated and self.on_price_update:
                self.on_price_update(self.get_prices())
                
        except Exception:
            pass  # Ignore total failure, maintain last known prices
            
    def _run_loop(self):
        """Background loop to fetch real prices and apply fluctuations"""
        last_fetch = 0
        
        while self.running:
            current_time = time.time()
            
            # 1. Fetch real prices every 20 seconds
            if current_time - last_fetch >= 20.0:
                self._fetch_real_prices()
                last_fetch = current_time
                
            # 2. Apply micro fluctuations
            with self.lock:
                for symbol in self.STOCKS:
                    fluctuation = random.uniform(-0.3, 0.3)
                    new_price = self.prices[symbol] + fluctuation
                    # Ensure price doesn't drop below 0.01
                    if new_price < 0.01:
                        new_price = 0.01
                    
                    rounded_price = round(new_price, 2)
                    self.prices[symbol] = rounded_price
                    self._add_history(symbol, rounded_price)
                    
            # 3. Trigger callback to execute matching logic
            if self.on_price_update:
                self.on_price_update(self.get_prices())
                
            # Sleep for 2-3 seconds before next fluctuation
            time.sleep(random.uniform(2.0, 3.0))
