#include "avl_tree.h"

AVLTree::~AVLTree() {
    clear(root);
}

void AVLTree::clear(AVLNode *node) {
    if (node) {
        clear(node->left);
        clear(node->right);
        delete node;
    }
}

int AVLTree::height(AVLNode *n) {
    return n ? n->height : 0;
}

int AVLTree::getBalance(AVLNode *n) {
    return n ? height(n->left) - height(n->right) : 0;
}

AVLNode* AVLTree::rightRotate(AVLNode *y) {
    AVLNode *x = y->left;
    AVLNode *T2 = x->right;

    x->right = y;
    y->left = T2;

    y->height = std::max(height(y->left), height(y->right)) + 1;
    x->height = std::max(height(x->left), height(x->right)) + 1;

    return x;
}

AVLNode* AVLTree::leftRotate(AVLNode *x) {
    AVLNode *y = x->right;
    AVLNode *T2 = y->left;

    y->left = x;
    x->right = T2;

    x->height = std::max(height(x->left), height(x->right)) + 1;
    y->height = std::max(height(y->left), height(y->right)) + 1;

    return y;
}

void AVLTree::insert(double price, Order order) {
    root = insert(root, price, order);
}

AVLNode* AVLTree::insert(AVLNode *node, double price, Order order) {
    if (!node) return new AVLNode(price, order);

    if (price < node->price)
        node->left = insert(node->left, price, order);
    else if (price > node->price)
        node->right = insert(node->right, price, order);
    else {
        node->orders.push_back(order);
        return node;
    }

    node->height = 1 + std::max(height(node->left), height(node->right));

    int balance = getBalance(node);

    if (balance > 1 && price < node->left->price)
        return rightRotate(node);

    if (balance < -1 && price > node->right->price)
        return leftRotate(node);

    if (balance > 1 && price > node->left->price) {
        node->left = leftRotate(node->left);
        return rightRotate(node);
    }

    if (balance < -1 && price < node->right->price) {
        node->right = rightRotate(node->right);
        return leftRotate(node);
    }

    return node;
}

AVLNode* AVLTree::minValueNode(AVLNode *node) {
    AVLNode *current = node;
    while (current->left != nullptr)
        current = current->left;
    return current;
}

void AVLTree::remove(double price) {
    root = deleteNode(root, price);
}

AVLNode* AVLTree::deleteNode(AVLNode *root, double price) {
    if (!root) return root;

    if (price < root->price)
        root->left = deleteNode(root->left, price);
    else if (price > root->price)
        root->right = deleteNode(root->right, price);
    else {
        if ((root->left == nullptr) || (root->right == nullptr)) {
            AVLNode *temp = root->left ? root->left : root->right;

            if (!temp) {
                temp = root;
                root = nullptr;
            } else
                *root = *temp;
            delete temp;
        } else {
            AVLNode *temp = minValueNode(root->right);
            root->price = temp->price;
            root->orders = temp->orders;
            root->right = deleteNode(root->right, temp->price);
        }
    }

    if (!root) return root;

    root->height = 1 + std::max(height(root->left), height(root->right));

    int balance = getBalance(root);

    if (balance > 1 && getBalance(root->left) >= 0)
        return rightRotate(root);

    if (balance > 1 && getBalance(root->left) < 0) {
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }

    if (balance < -1 && getBalance(root->right) <= 0)
        return leftRotate(root);

    if (balance < -1 && getBalance(root->right) > 0) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
    }

    return root;
}

AVLNode* AVLTree::get_min() {
    if (!root) return nullptr;
    AVLNode *current = root;
    while (current->left) current = current->left;
    return current;
}

AVLNode* AVLTree::get_max() {
    if (!root) return nullptr;
    AVLNode *current = root;
    while (current->right) current = current->right;
    return current;
}

void AVLTree::inorder(std::vector<AVLNode*>& nodes) {
    inorder(root, nodes);
}

void AVLTree::inorder(AVLNode *root, std::vector<AVLNode*>& nodes) {
    if (root) {
        inorder(root->left, nodes);
        nodes.push_back(root);
        inorder(root->right, nodes);
    }
}
