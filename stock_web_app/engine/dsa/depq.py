import heapq

class DEPQ:
    """
    Double-Ended Priority Queue using two heaps.
    Used for quick access to best bid and best ask.
    """
    def __init__(self):
        self.min_heap = [] # (price, order_id)
        self.max_heap = [] # (-price, order_id)
        self.deleted_ids = set()

    def insert(self, price, order_id):
        heapq.heappush(self.min_heap, (price, order_id))
        heapq.heappush(self.max_heap, (-price, order_id))

    def get_max(self):
        self._clean_max()
        if not self.max_heap:
            return None
        return -self.max_heap[0][0]

    def get_min(self):
        self._clean_min()
        if not self.min_heap:
            return None
        return self.min_heap[0][0]

    def remove(self, order_id):
        self.deleted_ids.add(order_id)

    def _clean_max(self):
        while self.max_heap and self.max_heap[0][1] in self.deleted_ids:
            item = heapq.heappop(self.max_heap)
            self.deleted_ids.remove(item[1])

    def _clean_min(self):
        while self.min_heap and self.min_heap[0][1] in self.deleted_ids:
            item = heapq.heappop(self.min_heap)
            self.deleted_ids.remove(item[1])
