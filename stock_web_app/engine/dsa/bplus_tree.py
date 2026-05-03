import bisect

class BPlusTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.values = [] # Only for leaf nodes
        self.children = [] # Only for internal nodes
        self.next = None # Link to next leaf node

class BPlusTree:
    def __init__(self, order=4):
        self.root = BPlusTreeNode(leaf=True)
        self.order = order

    def insert(self, key, value):
        root = self.root
        if len(root.keys) == self.order:
            new_root = BPlusTreeNode()
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, value)

    def _split_child(self, parent, i):
        order = self.order
        node = parent.children[i]
        new_node = BPlusTreeNode(leaf=node.leaf)
        
        mid = order // 2
        split_key = node.keys[mid]
        
        parent.keys.insert(i, split_key)
        parent.children.insert(i + 1, new_node)
        
        new_node.keys = node.keys[mid:]
        node.keys = node.keys[:mid]
        
        if node.leaf:
            new_node.values = node.values[mid:]
            node.values = node.values[:mid]
            new_node.next = node.next
            node.next = new_node
        else:
            new_node.children = node.children[mid:]
            node.children = node.children[:mid]

    def _insert_non_full(self, node, key, value):
        if node.leaf:
            idx = bisect.bisect_left(node.keys, key)
            if idx < len(node.keys) and node.keys[idx] == key:
                node.values[idx].append(value)
            else:
                node.keys.insert(idx, key)
                node.values.insert(idx, [value])
        else:
            idx = bisect.bisect_right(node.keys, key)
            if len(node.children[idx].keys) == self.order:
                self._split_child(node, idx)
                if key > node.keys[idx]:
                    idx += 1
            self._insert_non_full(node.children[idx], key, value)

    def search(self, key):
        node = self.root
        while not node.leaf:
            idx = bisect.bisect_right(node.keys, key)
            node = node.children[idx]
        
        idx = bisect.bisect_left(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            return node.values[idx]
        return []

    def get_range(self, start_key, end_key):
        results = []
        node = self.root
        while not node.leaf:
            idx = bisect.bisect_right(node.keys, start_key)
            node = node.children[idx]
        
        while node:
            for i, key in enumerate(node.keys):
                if key > end_key:
                    return results
                if key >= start_key:
                    results.extend(node.values[i])
            node = node.next
        return results
