import collections
import logging
from typing import Dict, List

Point = collections.namedtuple('Point', ['x', 'y'])


class ChooseStrategy(object):

    def __init__(self):
        pass

    def chooseOne(self, args: ['Element']) -> 'Element':
        pass


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

    def __init__(self, p: Point, n: int):
        assert n > p.x > -1 and n > p.y > -1
        self.point: Point = p
        self.grid_size: int = n

    def canDisplace(self, o: 'Element') -> bool:
        pass

    def isNeighbour(self, o: 'Element') -> bool:
        if o.point in self.getNeighbours():
            return True
        return False

    def getNeighbours(self) -> [Point]:
        """

        :return: A list of Points
        """
        n = []
        x = self.point.x
        y = self.point.y

        # north
        if y - 1 >= 0:
            n.append(Point(x, y - 1))
        # south
        if y + 1 < self.grid_size:
            n.append(Point(x, y + 1))

        # east
        if x + 1 < self.grid_size:
            n.append(Point(x + 1, y))

        # west
        if x - 1 >= 0:
            n.append(Point(x - 1, y))
        return n

    def getExtendedNeighbours(self) -> [Point]:
        """

        :return: A tuple of Points
        """
        n = []
        x = self.point.x
        y = self.point.y

        # north
        if y - 1 >= 0:
            n.append(Point(x, y - 1))
        # south
        if y + 1 < self.grid_size:
            n.append(Point(x, y + 1))

        # east
        if x + 1 < self.grid_size:
            n.append(Point(x + 1, y))

        # west
        if x - 1 >= 0:
            n.append(Point(x - 1, y))
        return n

    def chooseNeighbour(self, chooser: ChooseStrategy) -> 'Element':
        return chooser.chooseOne(self.getNeighbours())

    def swap(self, o: 'Element'):
        temp = o.point
        o.point = self.point
        self.point = temp

    def __repr__(self):
        return '{0}:({1},{2})'.format(self.__class__.__name__, self.point.x, self.point.y)

    def __eq__(self, other):
        if type(self) == type(other) and self.point == other.point:
            return True
        return False


class Hole(Element):

    def chooseNeighbour(self, chooser: ChooseStrategy) -> Element:
        return super().chooseNeighbour(chooser)

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        return False


class Substrate(Element):

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        if isinstance(o, Hole):
            return True
        else:
            return False


class Catalyst(Element):

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        # TODO: Consider bonded links cannot be broken
        if isinstance(o, (Hole, Substrate, Link)):
            return True
        else:
            return False


class Link(Element):

    def __init__(self, p: Point, n: int):
        super().__init__(p, n)

    def canDisplace(self, o):
        if isinstance(o, (Hole, Substrate)):
            return True
        else:
            return False

    def isFree(self):
        # TODO: fixme
        return True


# base class for creating the overall algorithm
class Process(object):

    def __init__(self,
                 grid: Dict[Point, Element],
                 hole_list: List[Hole],
                 substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst],
                 link_list: [List],
                 choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        self.grid: Dict[Point, Element] = grid
        self.h_list: List[Hole] = hole_list
        self.s_list: List[substrate_list] = substrate_list
        self.k_list: List[Catalyst] = catalyst_list
        self.l_list: List[Link] = link_list
        self.chooser: ChooseStrategy = choose_strategy
        self.logger: logging.Logger = logger

    def swap(self, this: Element, other: Element):
        assert this.isNeighbour(other)
        temp = self.grid[this.point]
        self.grid[this.point] = other
        self.grid[other.point] = temp
        this.swap(other)

    def doStep(self):
        self.logger.error('doStep() not implemented')


class HoleProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doStep(self):
        for hole in self.h_list:
            n = self.grid[hole.chooseNeighbour(self.chooser)]
            # 1.30
            if isinstance(n, (Substrate, Catalyst)):
                self.swap(hole, n)
            elif isinstance(n, Link):
                if n.isFree():
                    self.swap(hole, n)
            # 1.31
            elif isinstance(n, Hole):
                # do nothing
                continue
            # 1.32
            # TODO: Add bonded L routine


class WorldModel(object):

    def __init__(self, choose_strategy):
        self.choose_strategy = choose_strategy
