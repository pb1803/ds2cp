#include "bplus_tree.h"
#include "order_engine.h" // For Trade struct

void BPlusTree::insert(std::string key, Trade* trade) {
    if (root == nullptr) {
        root = new BPlusNode(true);
        root->keys.push_back(key);
        root->trades.push_back(trade);
        return;
    }

    BPlusNode* cursor = root;
    BPlusNode* parent = nullptr;

    while (!cursor->isLeaf) {
        parent = cursor;
        for (int i = 0; i < cursor->keys.size(); i++) {
            if (key < cursor->keys[i]) {
                cursor = cursor->children[i];
                goto next_node;
            }
            if (i == cursor->keys.size() - 1) {
                cursor = cursor->children[i + 1];
                goto next_node;
            }
        }
    next_node:;
    }

    auto it = std::upper_bound(cursor->keys.begin(), cursor->keys.end(), key);
    int idx = std::distance(cursor->keys.begin(), it);
    cursor->keys.insert(it, key);
    cursor->trades.insert(cursor->trades.begin() + idx, trade);

    if (cursor->keys.size() > MAX_KEYS) {
        BPlusNode* newLeaf = new BPlusNode(true);
        int mid = (MAX_KEYS + 1) / 2;
        
        newLeaf->keys.assign(cursor->keys.begin() + mid, cursor->keys.end());
        newLeaf->trades.assign(cursor->trades.begin() + mid, cursor->trades.end());
        cursor->keys.resize(mid);
        cursor->trades.resize(mid);

        newLeaf->next = cursor->next;
        cursor->next = newLeaf;

        if (cursor == root) {
            BPlusNode* newRoot = new BPlusNode(false);
            newRoot->keys.push_back(newLeaf->keys[0]);
            newRoot->children.push_back(cursor);
            newRoot->children.push_back(newLeaf);
            root = newRoot;
        } else {
            insertInternal(newLeaf->keys[0], parent, newLeaf);
        }
    }
}

void BPlusTree::insertInternal(std::string key, BPlusNode* cursor, BPlusNode* child) {
    auto it = std::upper_bound(cursor->keys.begin(), cursor->keys.end(), key);
    int idx = std::distance(cursor->keys.begin(), it);
    cursor->keys.insert(it, key);
    cursor->children.insert(cursor->children.begin() + idx + 1, child);

    if (cursor->keys.size() > MAX_KEYS) {
        BPlusNode* newNode = new BPlusNode(false);
        int mid = cursor->keys.size() / 2;
        std::string midKey = cursor->keys[mid];

        newNode->keys.assign(cursor->keys.begin() + mid + 1, cursor->keys.end());
        newNode->children.assign(cursor->children.begin() + mid + 1, cursor->children.end());
        
        cursor->keys.resize(mid);
        cursor->children.resize(mid + 1);

        if (cursor == root) {
            BPlusNode* newRoot = new BPlusNode(false);
            newRoot->keys.push_back(midKey);
            newRoot->children.push_back(cursor);
            newRoot->children.push_back(newNode);
            root = newRoot;
        } else {
            insertInternal(midKey, findParent(root, cursor), newNode);
        }
    }
}

BPlusNode* BPlusTree::findParent(BPlusNode* cursor, BPlusNode* child) {
    BPlusNode* parent = nullptr;
    if (cursor->isLeaf || cursor->children[0]->isLeaf) return nullptr;

    for (int i = 0; i < cursor->children.size(); i++) {
        if (cursor->children[i] == child) return cursor;
        else {
            parent = findParent(cursor->children[i], child);
            if (parent != nullptr) return parent;
        }
    }
    return nullptr;
}

std::vector<Trade*> BPlusTree::rangeSearch(std::string start, std::string end) {
    std::vector<Trade*> results;
    if (root == nullptr) return results;

    BPlusNode* cursor = root;
    while (!cursor->isLeaf) {
        for (int i = 0; i < cursor->keys.size(); i++) {
            if (start < cursor->keys[i]) {
                cursor = cursor->children[i];
                goto find_leaf;
            }
            if (i == cursor->keys.size() - 1) {
                cursor = cursor->children[i + 1];
                goto find_leaf;
            }
        }
    find_leaf:;
    }

    bool finished = false;
    while (cursor != nullptr && !finished) {
        for (int i = 0; i < cursor->keys.size(); i++) {
            if (cursor->keys[i] >= start && cursor->keys[i] <= end) {
                results.push_back(cursor->trades[i]);
            } else if (cursor->keys[i] > end) {
                finished = true;
                break;
            }
        }
        cursor = cursor->next;
    }
    return results;
}
