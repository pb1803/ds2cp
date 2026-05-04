# Advanced DSA Trading Engine (Python-C++ Hybrid)

This document explains the advanced Data Structures and Algorithms (DSA) implemented in the C++ core engine of the stock trading application.

---

## SECTION 1: Why C++ for DSA?

In high-frequency trading systems, performance is critical. While Python is excellent for building web APIs and handling UI, its global interpreter lock (GIL) and dynamic nature can be bottlenecks for core computational logic. 

**Advantages of C++ for the Trading Engine:**
*   **Memory Efficiency:** Precise control over memory allocation for tree nodes.
*   **Speed:** Compiled machine code executes significantly faster than interpreted Python.
*   **Determinism:** Predictable performance without garbage collection pauses.
*   **Advanced DSA Implementation:** Native support for pointers and complex memory layouts allows for more robust implementations of custom data structures.

---

## SECTION 2: Structures Used

### 1. AVL Tree (Order Book)
*   **Implementation:** `engine_cpp/avl_tree.cpp`
*   **Role:** Manages the order book for each stock.
*   **Logic:** Nodes are keyed by **price**. Each node contains a `std::vector` of `Order` objects representing orders at that specific price level (FIFO).
*   **Complexity:** Guaranteed $O(\log n)$ for insertion, deletion, and search by price.

### 2. DEPQ (Double-Ended Priority Queue)
*   **Implementation:** `engine_cpp/depq.cpp`
*   **Role:** Provides efficient access to the "Best Bid" (highest buy price) and "Best Ask" (lowest sell price).
*   **Logic:** Implemented using the **AVL Tree** internally. Since an AVL tree is sorted, retrieving the minimum and maximum elements is a simple traversal to the leftmost and rightmost nodes.
*   **Complexity:** $O(\log n)$ to find min/max in the AVL-based implementation.

### 3. Trie (Prefix Tree)
*   **Implementation:** `engine_cpp/trie.cpp`
*   **Role:** Efficient stock symbol searching and prefix matching.
*   **Logic:** Stores characters of stock symbols in a tree structure. Each node contains a map of child characters.
*   **Complexity:** $O(L)$ where $L$ is the length of the search query, regardless of the number of symbols.

---

## SECTION 3: Flow of Execution

1.  **Order Placement:**
    *   Python (Flask) receives a POST request.
    *   The data is serialized to JSON and sent to the C++ engine via `stdin`.
    *   C++ engine parses the JSON and inserts the order into the corresponding symbol's **AVL Tree**.
2.  **Order Storage:**
    *   Orders are grouped by price level within the AVL tree.
    *   The tree remains balanced automatically through rotations.
3.  **Execution Logic:**
    *   When market prices update, Flask sends the new prices to the C++ engine.
    *   The engine performs an **inorder traversal** of the AVL Trees.
    *   **Cross Logic:** If a BUY order's price is $\ge$ Market Price OR a SELL order's price is $\le$ Market Price, a trade is executed.
    *   Executed orders are removed from the trees, and `Trade` objects are generated.

---

## SECTION 4: Complexity Analysis

| Operation | Data Structure | Time Complexity |
| :--- | :--- | :--- |
| Place Order | AVL Tree | $O(\log n)$ |
| Cancel Order | AVL Tree | $O(\log n)$ |
| Get Best Price | DEPQ (AVL) | $O(\log n)$ |
| Symbol Search | Trie | $O(L)$ |
| Matching Traversal | AVL Tree | $O(k \log n)$ |

*where $n$ is the number of price levels, $L$ is query length, and $k$ is number of matches.*

---

## SECTION 5: Python ↔ C++ Integration

The integration uses a **Persistent Subprocess Bridge**:

1.  **Backend Initialization:** Flask starts the `engine.exe` process once.
2.  **Communication:** Flask uses `subprocess.PIPE` to communicate via `stdin` and `stdout`.
3.  **Data Format:** All messages are sent as single-line JSON objects.
    *   **Request (Python -> C++):** `{"action": "place_order", "symbol": "TCS.NS", ...}`
    *   **Response (C++ -> Python):** `{"status": "success", "order_id": "ORD-1"}`
4.  **State Management:** The C++ process maintains the entire state of the order book and trade history in memory for the duration of the server's uptime.

---

## SECTION 6: Build & Run

### Compilation
To compile the C++ engine, use the following command in the `engine_cpp/` directory:

```powershell
g++ main.cpp order_engine.cpp avl_tree.cpp depq.cpp trie.cpp -o engine.exe -std=c++11
```

### Running the App
Once compiled, simply start the Flask application:

```powershell
python app.py
```
### 4. B+ Tree (Trade History Indexing)
*   **Purpose**: Efficiently stores and retrieves trade history records.
*   **Performance**:
    *   **Insertion**: $O(\log n)$
    *   **Range Query**: $O(\log n + k)$ where $k$ is the number of results.
*   **Usage**: The `BPlusTree` in C++ allows for high-speed range queries (e.g., "all trades between 10:00 AM and 11:00 AM") which is essential for audit trails and historical analysis.

### 5. Technical Indicators (Sliding Window)
*   **Purpose**: Real-time calculation of market trends.
*   **Logic**:
    *   **SMA (Simple Moving Average)**: Calculated using a sliding window of the last 14-50 prices stored in a `std::deque`.
    *   **RSI (Relative Strength Index)**: Measures the speed and change of price movements to identify overbought or oversold conditions.
*   **Performance**: $O(p)$ where $p$ is the period length, calculated instantly on every price update.

---

## 🚀 Real-Time Architecture (WebSocket)
The system now utilizes **Flask-SocketIO** for a true real-time experience:
1.  **C++ Engine**: Processes trades and emits events.
2.  **Python Layer**: Forwards these events to the frontend via WebSockets.
3.  **Frontend**: Instantly updates the chart, order book, and shows **Trade Execution Notifications** in the top-right corner without any page refresh or polling.
