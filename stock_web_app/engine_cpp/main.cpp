#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <chrono>
#include "order_engine.h"

// Simple helper to parse basic JSON-like input (key-value pairs)
// Since we are using stdin/stdout, we can assume one JSON object per line.
// This is a minimal implementation for the task requirements.

std::string get_json_value(const std::string& json, const std::string& key) {
    size_t pos = json.find("\"" + key + "\"");
    if (pos == std::string::npos) return "";
    pos = json.find(":", pos);
    if (pos == std::string::npos) return "";
    
    size_t start = json.find_first_not_of(" ", pos + 1);
    if (start == std::string::npos) return "";
    
    if (json[start] == '"') {
        start++;
        size_t end = json.find("\"", start);
        if (end == std::string::npos) return "";
        return json.substr(start, end - start);
    } else {
        size_t end = json.find_first_of(",} ", start);
        if (end == std::string::npos) return json.substr(start);
        return json.substr(start, end - start);
    }
}

int main() {
    std::vector<std::string> symbols = {
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
        "BHARTIARTL.NS", "SBIN.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS"
    };

    OrderEngine engine(symbols);
    std::string line;

    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;

        try {
            std::string action = get_json_value(line, "action");

            if (action == "place_order") {
                std::string symbol = get_json_value(line, "symbol");
                std::string type = get_json_value(line, "type");
                double price = std::stod(get_json_value(line, "price"));
                int quantity = std::stoi(get_json_value(line, "quantity"));

                auto start = std::chrono::high_resolution_clock::now();
                std::string id = engine.placeOrder(symbol, type, price, quantity);
                auto end = std::chrono::high_resolution_clock::now();
                
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
                std::cout << "{\"status\":\"success\",\"order_id\":\"" << id << "\",\"exec_time_us\":" << duration << "}" << std::endl;
            } 
            else if (action == "process_market_orders") {
                std::unordered_map<std::string, double> prices;
                for (const auto& s : symbols) {
                    std::string p_str = get_json_value(line, s);
                    if (!p_str.empty()) prices[s] = std::stod(p_str);
                }
                
                auto start = std::chrono::high_resolution_clock::now();
                auto trades = engine.processMarketOrders(prices);
                auto end = std::chrono::high_resolution_clock::now();
                
                auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
                
                std::cout << "{\"status\":\"success\",\"executed_count\":" << trades.size() << ",\"exec_time_us\":" << duration << ",\"trades\":[";
                for (size_t i = 0; i < trades.size(); ++i) {
                    const auto& t = *trades[i];
                    std::cout << "{\"trade_id\":\"" << t.trade_id << "\",\"symbol\":\"" << t.symbol << "\",\"type\":\"" << t.type << "\",\"exec_price\":" << t.exec_price << ",\"quantity\":" << t.quantity << "}";
                    if (i < trades.size() - 1) std::cout << ",";
                }
                std::cout << "]}" << std::endl;
            }
            else if (action == "get_order_book") {
                auto book = engine.getOrderBook();
                std::cout << "{\"status\":\"success\",\"buy_side\":[";
                bool first = true;
                for (auto& node_list : book["buy"]) {
                    for (auto& o : node_list) {
                        if (!first) std::cout << ",";
                        std::cout << "{\"id\":\"" << o.id << "\",\"symbol\":\"" << o.symbol << "\",\"price\":" << o.price << ",\"quantity\":" << o.quantity << "}";
                        first = false;
                    }
                }
                std::cout << "],\"sell_side\":[";
                first = true;
                for (auto& node_list : book["sell"]) {
                    for (auto& o : node_list) {
                        if (!first) std::cout << ",";
                        std::cout << "{\"id\":\"" << o.id << "\",\"symbol\":\"" << o.symbol << "\",\"price\":" << o.price << ",\"quantity\":" << o.quantity << "}";
                        first = false;
                    }
                }
                std::cout << "]}" << std::endl;
            }
            else if (action == "get_trades") {
            std::string start = get_json_value(line, "start");
            std::string end = get_json_value(line, "end");
            auto trades = engine.getTrades(start, end);
            std::cout << "{\"status\":\"success\",\"trades\":[";
            for (size_t i = 0; i < trades.size(); ++i) {
                const auto& t = *trades[i];
                std::cout << "{\"trade_id\":\"" << t.trade_id << "\",\"order_id\":\"" << t.order_id << "\",\"symbol\":\"" << t.symbol << "\",\"type\":\"" << t.type << "\",\"limit_price\":" << t.limit_price << ",\"exec_price\":" << t.exec_price << ",\"order_price\":" << t.limit_price << ",\"market_price\":" << t.exec_price << ",\"quantity\":" << t.quantity << ",\"timestamp\":\"" << t.timestamp << "\"}";
                if (i < trades.size() - 1) std::cout << ",";
            }
            std::cout << "]}" << std::endl;
        }
        else if (action == "get_indicators") {
            std::string symbol = get_json_value(line, "symbol");
            double sma = engine.calculateSMA(symbol, 14);
            double rsi = engine.calculateRSI(symbol, 14);
            std::cout << "{\"status\":\"success\",\"sma\":" << sma << ",\"rsi\":" << rsi << "}" << std::endl;
        }
            else if (action == "get_stats") {
                auto stats = engine.getStats();
                std::cout << "{\"status\":\"success\",\"stats\":{";
                bool first = true;
                for (auto const& pair : stats) {
                    if (!first) std::cout << ",";
                    std::cout << "\"" << pair.first << "\":" << pair.second;
                    first = false;
                }
                std::cout << "}}" << std::endl;
            }
            else if (action == "search_symbols") {
                std::string query = get_json_value(line, "query");
                auto results = engine.searchSymbols(query);
                std::cout << "{\"status\":\"success\",\"results\":[";
                for (size_t i = 0; i < results.size(); ++i) {
                    std::cout << "\"" << results[i] << "\"";
                    if (i < results.size() - 1) std::cout << ",";
                }
                std::cout << "]}" << std::endl;
            }
            else if (action == "exit") {
                break;
            }
        } catch (const std::exception& e) {
            std::cout << "{\"status\":\"error\",\"message\":\"" << e.what() << "\"}" << std::endl;
        }
    }

    return 0;
}
