import queue


class Partitioner():
    def __init__(self, items):
        self.list = items

    def run(self):
        q = queue.Queue()
        entry = None
        for item in sorted(self.list, reverse=True):
            node = Node(item)
            q.put(node)
            if q.qsize() == 2:
                entry = node

        while q.qsize() > 1:
            print("Linking:")
            item1 = q.get()
            print(item1)
            item2 = q.get()
            print(item2)
            print("right")
            print(item1.left)
            print("\n\n")

            link = LinkNode(item1, item2)

            if q.qsize() == 0:
                print("outputting")
                link.output()
            print(link)
            print("\n\n\n\n")
            q.put(link)

        print(entry)
        print(entry.right)


def link(l, r):
    print("Permalinking {} and {}".format(str(l), str(r)))
    setattr(l, "permaright", r)
    setattr(r, "permaleft", l)


class Node():
    right = None
    left = None
    permaright = None
    permaleft = None

    def __str__(self):
        return str(self.value())

    def __init__(self, number):
        self.val = number
        self.right = None
        self.left = None

    def value(self):
        return self.val

    def node(self):
        return self

    def output(self):
        pass

    def has_right(self):
        return hasattr(self, "right")

    def get_left(self):
        return self.permaleft

    def get_right(self):
        return self.permaright


class LinkNode():
    right = None
    left = None
    permaright = None
    permaleft = None

    def __str__(self):
        return "Left: {left}, Right: {right}".format(left=self.left.__str__(), right=self.right.__str__())

    def __init__(self, left, right):
        self.left = left
        self.right = right

        if self.left.value() > self.right.value():
            self.repr = self.left
        else:
            self.repr = self.right
        link(left.node(), right.node())

    def value(self):
        return abs(self.left.value() - self.right.value())

    def get_left(self):
        return self.left

    def get_right(self):
        return self.right

    def output(self):
        print("getting links")
        item = self
        while item.get_left():
            # print("AA:" + str(item))
            item = item.get_left()
        while item.get_right():
            print("AA:" + str(item))
            item = item.get_right()

    def node(self):
        return self.repr
