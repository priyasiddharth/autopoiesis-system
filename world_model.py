# TODO: Do I need to mark cells as non-existent to help debugging?
class Element(object):
    """Base class common to L, K, S and H

    Assume grid is laid out in the following manner.
    ----x-->(n-1)
    |
    |
    y
    |
    v
    (n-1)
    """

    def __init__(self, x, y, n):
        assert n > x > -1 and n > y > -1
        self.x = x
        self.y = y
        self.grid_size = n

    def canDisplace(self, o):
        pass

    def getNeighbours(self):
        """

        :return: A tuple of co-ordinates
        """
        n = []
        x = self.x
        y = self.y

        # north
        if y - 1 >= 0:
            n.append((x, y - 1))
        # south
        if y + 1 < self.grid_size:
            n.append((x, y + 1))

        # east
        if x + 1 < self.grid_size:
            n.append((x + 1, y))

        # west
        if x - 1 >= 0:
            n.append((x - 1, y))
        return n


class Hole(Element):

    def __init__(self, x, y, n):
        super().__init__(x, y, n)

    def canDisplace(self, o):
        return False


class Substrate(Element):

    def __init__(self, x, y, n):
        super().__init__(x, y, n)

    def canDisplace(self, o):
        if isinstance(o, Hole):
            return True
        else:
            return False


class Catalyst(Element):

    def __init__(self, x, y, n):
        super().__init__(x, y, n)

    def canDisplace(self, o):
        # TODO: Consider bonded links cannot be broken
        if isinstance(o, (Hole, Substrate, Link)):
            return True
        else:
            return False


class Link(Element):

    def __init__(self, x, y, n):
        super().__init__(x, y, n)

    def canDisplace(self, o):
        if isinstance(o, (Hole, Substrate)):
            return True
        else:
            return False


class WorlModel(object):

    def __init__(self):
        pass
