# Advanced Data Structures in ProTrade Terminal

This document outlines the advanced Data Structures and Algorithms (DSA) implemented in the ProTrade Terminal to enhance performance, scalability, and academic depth.

---

## SECTION 1: Overview

In real-world high-frequency trading (HFT) systems, speed and efficiency are paramount. Basic data structures like lists or simple dictionaries often fall short when handling millions of orders and trades per second. By utilizing specialized data structures like AVL Trees, Tries, and B+ Trees, we ensure that the system remains responsive even under high load, with predictable time complexities for core operations.

---

## SECTION 2: Data Structures Used

### 1. AVL Tree (Self-Balancing Binary Search Tree)
- **Where Used**: Order Book management (`engine/order_engine.py`).
- **Why Used**: To maintain orders in a sorted state by price. Unlike a regular BST, an AVL tree guarantees $O(\log n)$ height by performing rotations during insertion and deletion. This ensures that finding the best bid or ask always takes logarithmic time.
- **Node Structure**:
  - `key`: Price level.
  - `value`: A list of orders at that specific price (FIFO).
- **Time Complexity**:
  - Insertion: $O(\log n)$
  - Deletion: $O(\log n)$
  - Search: $O(\log n)$

### 2. DEPQ (Double-Ended Priority Queue)
- **Where Used**: Instant access to best Bid and best Ask.
- **Why Used**: While AVL trees give us sorted access, a DEPQ (implemented using a Min-Heap and a Max-Heap) provides a highly efficient way to fetch the extreme values (highest buy and lowest sell) which are the most critical data points in a matching engine.
- **Time Complexity**:
  - Get Max/Min: $O(1)$ (top of heap)
  - Insertion: $O(\log n)$

### 3. Trie (Prefix Tree)
- **Where Used**: Stock symbol search and autocomplete (`/api/search`).
- **Why Used**: Tries are optimized for prefix-based searches. In a trading terminal, users often search for stocks by typing the first few letters. A Trie allows us to find all matching symbols in $O(L)$ time, where $L$ is the length of the query, regardless of how many thousands of stocks are in the system.
- **Time Complexity**:
  - Search/Insert: $O(L)$

### 4. B+ Tree
- **Where Used**: Trade History indexing (`engine/dsa/bplus_tree.py`).
- **Why Used**: Executed trades are often queried over time ranges. A B+ Tree stores data in its leaf nodes, which are linked together. This makes it exceptionally efficient for range queries (e.g., "Get all trades between 10:00 AM and 11:00 AM").
- **Time Complexity**:
  - Point Query: $O(\log_m n)$
  - Range Query: $O(\log_m n + k)$ (where $k$ is the number of results).

---

## SECTION 3: Comparison

| Operation | Old (List/Dict) | New (Advanced DSA) | Improvement |
| :--- | :--- | :--- | :--- |
| **Order Insertion** | $O(1)$ (Append) | $O(\log n)$ (AVL) | Maintains sorted order automatically |
| **Best Price Access** | $O(n \log n)$ (Sort) | $O(1)$ (DEPQ) | Drastic improvement for HFT |
| **Symbol Search** | $O(n)$ (Linear) | $O(L)$ (Trie) | Independent of symbol count |
| **Range Queries** | $O(n)$ (Filter) | $O(\log n + k)$ (B+ Tree) | Optimized for history retrieval |

---

## SECTION 4: Flow of Execution

1. **Order Placement**:
   - User submits a `BUY` order for `TCS.NS` at `₹3400`.
   - The engine inserts the order into the `TCS.NS` **AVL Tree** ($O(\log n)$).
   - The order is also pushed into the **DEPQ** for quick top-price tracking.
2. **Order Matching**:
   - The `PriceManager` thread updates the market price.
   - The engine performs an inorder traversal on the AVL Tree to find nodes whose prices cross the market price threshold.
   - Matching orders are executed and removed from the tree ($O(\log n)$).
3. **Trade Archiving**:
   - Executed trades are stored in the **B+ Tree** indexed by their ISO timestamp, enabling fast history lookups.

---

## SECTION 5: Complexity Analysis Summary

| Data Structure | Insertion | Deletion | Search |
| :--- | :--- | :--- | :--- |
| **AVL Tree** | $O(\log n)$ | $O(\log n)$ | $O(\log n)$ |
| **Trie** | $O(L)$ | $O(L)$ | $O(L)$ |
| **B+ Tree** | $O(\log_m n)$ | $O(\log_m n)$ | $O(\log_m n)$ |
| **DEPQ** | $O(\log n)$ | $O(\log n)$ | $O(1)$ (Top) |
