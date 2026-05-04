#ifndef BPLUS_TREE_H
#define BPLUS_TREE_H

#include <vector>
#include <string>
#include <iostream>
#include <algorithm>

const int MAX_KEYS = 4; // Low degree for testing, can be increased

struct Trade; // Forward declaration

struct BPlusNode {
    bool isLeaf;
    std::vector<std::string> keys;
    std::vector<BPlusNode*> children;
    std::vector<Trade*> trades;
    BPlusNode* next;

    BPlusNode(bool leaf) : isLeaf(leaf), next(nullptr) {}
};

class BPlusTree {
private:
    BPlusNode* root;
    void insertInternal(std::string key, BPlusNode* parent, BPlusNode* child);
    BPlusNode* findParent(BPlusNode* cursor, BPlusNode* child);

public:
    BPlusTree() : root(nullptr) {}
    void insert(std::string timestamp, Trade* trade);
    std::vector<Trade*> rangeSearch(std::string start, std::string end);
};

#endif
