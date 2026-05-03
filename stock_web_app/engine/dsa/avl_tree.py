class AVLNode:
    def __init__(self, price):
        self.price = price
        self.orders = [] # List of orders at this price
        self.height = 1
        self.left = None
        self.right = None

class AVLTree:
    def __init__(self):
        self.root = None

    def get_height(self, node):
        if not node:
            return 0
        return node.height

    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    def right_rotate(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        return x

    def left_rotate(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def insert(self, root, price, order):
        if not root:
            node = AVLNode(price)
            node.orders.append(order)
            return node
        
        if price == root.price:
            root.orders.append(order)
            return root
        elif price < root.price:
            root.left = self.insert(root.left, price, order)
        else:
            root.right = self.insert(root.right, price, order)

        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        balance = self.get_balance(root)

        # Left Left
        if balance > 1 and price < root.left.price:
            return self.right_rotate(root)
        # Right Right
        if balance < -1 and price > root.right.price:
            return self.left_rotate(root)
        # Left Right
        if balance > 1 and price > root.left.price:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)
        # Right Left
        if balance < -1 and price < root.right.price:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)

        return root

    def get_min_node(self, node):
        if node is None or node.left is None:
            return node
        return self.get_min_node(node.left)

    def get_max_node(self, node):
        if node is None or node.right is None:
            return node
        return self.get_max_node(node.right)

    def delete(self, root, price):
        if not root:
            return root
        
        if price < root.price:
            root.left = self.delete(root.left, price)
        elif price > root.price:
            root.right = self.delete(root.right, price)
        else:
            if root.left is None:
                temp = root.right
                root = None
                return temp
            elif root.right is None:
                temp = root.left
                root = None
                return temp
            
            temp = self.get_min_node(root.right)
            root.price = temp.price
            root.orders = temp.orders
            root.right = self.delete(root.right, temp.price)

        if root is None:
            return root

        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        balance = self.get_balance(root)

        if balance > 1 and self.get_balance(root.left) >= 0:
            return self.right_rotate(root)
        if balance > 1 and self.get_balance(root.left) < 0:
            root.left = self.left_rotate(root.left)
            return self.right_rotate(root)
        if balance < -1 and self.get_balance(root.right) <= 0:
            return self.left_rotate(root)
        if balance < -1 and self.get_balance(root.right) > 0:
            root.right = self.right_rotate(root.right)
            return self.left_rotate(root)

        return root

    def find(self, root, price):
        if not root or root.price == price:
            return root
        if price < root.price:
            return self.find(root.left, price)
        return self.find(root.right, price)

    def inorder(self, root, result):
        if root:
            self.inorder(root.left, result)
            result.append(root)
            self.inorder(root.right, result)
