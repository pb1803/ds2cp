#include "depq.h"

void DEPQ::insert(double price, Order order) {
    tree.insert(price, order);
}

void DEPQ::remove(double price) {
    tree.remove(price);
}

double DEPQ::get_min() {
    AVLNode* min_node = tree.get_min();
    return min_node ? min_node->price : -1.0;
}

double DEPQ::get_max() {
    AVLNode* max_node = tree.get_max();
    return max_node ? max_node->price : -1.0;
}

bool DEPQ::empty() {
    return tree.root == nullptr;
}
