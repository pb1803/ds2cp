#ifndef ORDER_ENGINE_H
#define ORDER_ENGINE_H

#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <deque>
#include "avl_tree.h"
#include "trie.h"
#include "depq.h"
#include "bplus_tree.h"

struct Trade {
    std::string trade_id;
    std::string order_id;
    std::string symbol;
    std::string type;
    double limit_price;
    double exec_price;
    int quantity;
    std::string timestamp;
};

class OrderEngine {
private:
    int order_counter;
    int trade_counter;
    std::unordered_map<std::string, AVLTree*> buy_trees;
    std::unordered_map<std::string, AVLTree*> sell_trees;
    Trie symbol_trie;
    std::vector<Trade*> all_trades;
    std::vector<std::string> stock_symbols;
    BPlusTree trade_index;

    // Sliding window for indicators
    std::unordered_map<std::string, std::deque<double>> price_history;
    const size_t MAX_WINDOW = 50;

    std::string current_time_str();

public:
    OrderEngine(std::vector<std::string> symbols);
    ~OrderEngine();

    std::string placeOrder(std::string symbol, std::string type, double price, int quantity);
    std::vector<Trade*> processMarketOrders(std::unordered_map<std::string, double> market_prices);
    std::map<std::string, std::vector<std::vector<Order>>> getOrderBook();
    std::vector<Trade*> getTrades(std::string start = "", std::string end = "");
    std::vector<std::string> searchSymbols(std::string prefix);
    std::unordered_map<std::string, long long> getStats();
    
    // Technical Indicators
    double calculateSMA(std::string symbol, int period);
    double calculateRSI(std::string symbol, int period);
};

#endif
