#ifndef AVL_TREE_H
#define AVL_TREE_H

#include <vector>
#include <string>
#include <algorithm>

struct Order {
    std::string id;
    std::string symbol;
    std::string type;
    double price;
    int quantity;
    std::string timestamp;
};

struct AVLNode {
    double price;
    std::vector<Order> orders;
    AVLNode *left;
    AVLNode *right;
    int height;

    AVLNode(double p, Order o) : price(p), left(nullptr), right(nullptr), height(1) {
        orders.push_back(o);
    }
};

class AVLTree {
public:
    AVLNode *root;

    AVLTree() : root(nullptr) {}
    ~AVLTree();

    void insert(double price, Order order);
    void remove(double price);
    AVLNode* get_min();
    AVLNode* get_max();
    void inorder(std::vector<AVLNode*>& nodes);

private:
    int height(AVLNode *n);
    int getBalance(AVLNode *n);
    AVLNode* rightRotate(AVLNode *y);
    AVLNode* leftRotate(AVLNode *x);
    AVLNode* insert(AVLNode *node, double price, Order order);
    AVLNode* minValueNode(AVLNode *node);
    AVLNode* deleteNode(AVLNode *root, double price);
    void inorder(AVLNode *root, std::vector<AVLNode*>& nodes);
    void clear(AVLNode *node);
};

#endif
