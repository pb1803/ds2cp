#ifndef DEPQ_H
#define DEPQ_H

#include "avl_tree.h"

class DEPQ {
private:
    AVLTree tree;

public:
    void insert(double price, Order order);
    void remove(double price);
    double get_min();
    double get_max();
    bool empty();
};

#endif
