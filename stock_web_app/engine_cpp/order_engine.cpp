#include "order_engine.h"
#include <chrono>
#include <iomanip>
#include <sstream>
#include <iostream>

OrderEngine::OrderEngine(std::vector<std::string> symbols) : order_counter(0), trade_counter(0), stock_symbols(symbols) {
    for (const std::string& symbol : symbols) {
        buy_trees[symbol] = new AVLTree();
        sell_trees[symbol] = new AVLTree();
        symbol_trie.insert(symbol);
    }
}

OrderEngine::~OrderEngine() {
    for (auto const& pair : buy_trees) delete pair.second;
    for (auto const& pair : sell_trees) delete pair.second;
    for (Trade* t : all_trades) delete t;
}

std::string OrderEngine::current_time_str() {
    auto now = std::chrono::system_clock::now();
    auto in_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&in_time_t), "%Y-%m-%dT%H:%M:%S");
    return ss.str();
}

std::string OrderEngine::placeOrder(std::string symbol, std::string type, double price, int quantity) {
    order_counter++;
    std::string order_id = "ORD-" + std::to_string(order_counter);

    Order order = {order_id, symbol, type, price, quantity, current_time_str()};

    if (type == "BUY") {
        buy_trees[symbol]->insert(price, order);
    } else {
        sell_trees[symbol]->insert(price, order);
    }

    return order_id;
}

std::vector<Trade*> OrderEngine::processMarketOrders(std::unordered_map<std::string, double> market_prices) {
    std::vector<Trade*> executed_trades;

    for (auto const& pair : market_prices) {
        std::string symbol = pair.first;
        double m_price = pair.second;

        // Update price history for indicators
        price_history[symbol].push_back(m_price);
        if (price_history[symbol].size() > MAX_WINDOW) {
            price_history[symbol].pop_front();
        }

        // Match BUY orders (Order Price >= Market Price)
        AVLTree* buy_tree = buy_trees[symbol];
        std::vector<AVLNode*> buy_nodes;
        buy_tree->inorder(buy_nodes);

        for (int i = buy_nodes.size() - 1; i >= 0; --i) {
            AVLNode* node = buy_nodes[i];
            if (node->price >= m_price) {
                for (const auto& order : node->orders) {
                    trade_counter++;
                    Trade* t = new Trade {
                        "TRD-" + std::to_string(trade_counter),
                        order.id, symbol, order.type, order.price, m_price, order.quantity, current_time_str()
                    };
                    executed_trades.push_back(t);
                    all_trades.push_back(t);
                    trade_index.insert(t->timestamp, t);
                }
                buy_tree->remove(node->price);
            }
        }

        // Match SELL orders (Order Price <= Market Price)
        AVLTree* sell_tree = sell_trees[symbol];
        std::vector<AVLNode*> sell_nodes;
        sell_tree->inorder(sell_nodes);

        for (AVLNode* node : sell_nodes) {
            if (node->price <= m_price) {
                for (const auto& order : node->orders) {
                    trade_counter++;
                    Trade* t = new Trade {
                        "TRD-" + std::to_string(trade_counter),
                        order.id, symbol, order.type, order.price, m_price, order.quantity, current_time_str()
                    };
                    executed_trades.push_back(t);
                    all_trades.push_back(t);
                    trade_index.insert(t->timestamp, t);
                }
                sell_tree->remove(node->price);
            }
        }
    }

    return executed_trades;
}

std::map<std::string, std::vector<std::vector<Order>>> OrderEngine::getOrderBook() {
    std::map<std::string, std::vector<std::vector<Order>>> book;
    std::vector<std::vector<Order>> buy_side;
    std::vector<std::vector<Order>> sell_side;

    for (const std::string& symbol : stock_symbols) {
        std::vector<AVLNode*> b_nodes;
        buy_trees[symbol]->inorder(b_nodes);
        for (auto* n : b_nodes) buy_side.push_back(n->orders);

        std::vector<AVLNode*> s_nodes;
        sell_trees[symbol]->inorder(s_nodes);
        for (auto* n : s_nodes) sell_side.push_back(n->orders);
    }
    
    book["buy"] = buy_side;
    book["sell"] = sell_side;
    return book;
}

std::vector<Trade*> OrderEngine::getTrades(std::string start, std::string end) {
    if (!start.empty() && !end.empty()) {
        return trade_index.rangeSearch(start, end);
    }
    return all_trades;
}

double OrderEngine::calculateSMA(std::string symbol, int period) {
    if (price_history[symbol].size() < (size_t)period) return -1.0;
    double sum = 0;
    auto it = price_history[symbol].rbegin();
    for (int i = 0; i < period; ++i, ++it) {
        sum += *it;
    }
    return sum / period;
}

double OrderEngine::calculateRSI(std::string symbol, int period) {
    if (price_history[symbol].size() < (size_t)period + 1) return -1.0;
    
    double gain = 0, loss = 0;
    auto it = price_history[symbol].rbegin();
    for (int i = 0; i < period; ++i) {
        double diff = *it - *(it + 1);
        if (diff > 0) gain += diff;
        else loss -= diff;
        ++it;
    }
    
    if (loss == 0) return 100.0;
    double rs = (gain / period) / (loss / period);
    return 100.0 - (100.0 / (1.0 + rs));
}

std::unordered_map<std::string, long long> OrderEngine::getStats() {
    long long total_buy_orders = 0;
    long long total_sell_orders = 0;
    long long total_buy_qty = 0;
    long long total_sell_qty = 0;

    for (const std::string& symbol : stock_symbols) {
        std::vector<AVLNode*> b_nodes;
        buy_trees[symbol]->inorder(b_nodes);
        for (auto* n : b_nodes) {
            total_buy_orders += n->orders.size();
            for (auto& o : n->orders) total_buy_qty += o.quantity;
        }

        std::vector<AVLNode*> s_nodes;
        sell_trees[symbol]->inorder(s_nodes);
        for (auto* n : s_nodes) {
            total_sell_orders += n->orders.size();
            for (auto& o : n->orders) total_sell_qty += o.quantity;
        }
    }

    std::unordered_map<std::string, long long> stats;
    stats["total_buy_orders"] = total_buy_orders;
    stats["total_sell_orders"] = total_sell_orders;
    stats["total_buy_quantity"] = total_buy_qty;
    stats["total_sell_quantity"] = total_sell_qty;
    stats["trades_executed"] = (long long)all_trades.size();
    
    long long volume = 0;
    for (size_t i = 0; i < all_trades.size(); ++i) volume += all_trades[i]->quantity;
    stats["total_volume"] = volume;

    return stats;
}

std::vector<std::string> OrderEngine::searchSymbols(std::string prefix) {
    return symbol_trie.search(prefix);
}
