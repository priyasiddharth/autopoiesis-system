import collections
import itertools
import logging
import math
import typing
from typing import Dict, List, TypeVar, Optional

Point = collections.namedtuple('Point', ['x', 'y'])

T = TypeVar('T', bound='Element')  # Declare type variable


class ChooseStrategy(object):

    def __init__(self):
        pass

    def chooseOne(self, args: [T]) -> Optional[T]:
        pass

    def shuffleList(self, args: [T]) -> [T]:
        """Returns a new 'shuffled' copy of the list.

        :param args:
        :return:
        """
        pass

    def flipWeightedCoin(self) -> bool:
        """ Returns True with some probability

        :return: True with some probability
        """
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
        self._grid_size: int = n

    def canDisplace(self, o: T) -> bool:
        pass

    def getGridSize(self) -> int:
        return self._grid_size

    def isNeighbour(self, o: T) -> bool:
        if o.point in self.getNeighbours():
            return True
        return False

    # TODO: this fn may not be needed
    def hasNeighbourOfType(self, c, grid: Dict[Point, T]) -> bool:
        nbours = self.getNeighbours()
        for n in nbours:
            n_o = grid[n]
            if isinstance(n_o, c):
                return True
        return False

    def getNeighboursOfType(self, c: typing.Type[T], grid: Dict[Point, T]) -> [T]:
        assert self.hasNeighbourOfType(c, grid)
        nbours = self.getNeighbours()
        l = []
        for n in nbours:
            n_o = grid[n]
            if isinstance(n_o, c):
                l.append(typing.cast(c, n_o))
        return l

    def getNeighbours(self) -> [Point]:
        return self._getNeighbours(1)

    def getOrthoNeighbours(self) -> [Point]:
        return self._getNeighbours(1, ortho=True)

    def _getNeighbours(self, d: int, ortho: bool = False) -> [Point]:
        """

          :return: A list of Points in 2D clockwise order
          """
        n = []
        x = self.point.x
        y = self.point.y

        # north
        if y - d >= 0:
            n.append(Point(x, y - d))

        # east
        if x + d < self._grid_size:
            n.append(Point(x + d, y))

        # south
        if y + d < self._grid_size:
            n.append(Point(x, y + d))

        # west
        if x - d >= 0:
            n.append(Point(x - d, y))

        if d < 2 and not ortho:
            # NW
            if y - d >= 0 and x - d >= 0:
                n.append(Point(x - d, y - d))
            # NE
            if y - d >= 0 and x + d < self._grid_size:
                n.append(Point(x + d, y - d))
            # SE
            if y + d < self._grid_size and x + d < self._grid_size:
                n.append(Point(x + d, y + d))
            # SW
            if y + d < self._grid_size and x - d >= 0:
                n.append(Point(x - d, y + d))
        return n

    def getExtendedNeighbours(self) -> [Point]:
        return self._getNeighbours(2)

    def chooseNeighbour(self, chooser: ChooseStrategy) -> T:
        return chooser.chooseOne(self.getNeighbours())

    def swap(self, o: T):
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

    @staticmethod
    def CreateSubstrate(x: int, y: int, n: int):
        return Substrate(Point(x, y), n)

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

    @staticmethod
    def CreateLink(x: int, y: int, n: int):
        return Link(Point(x, y), n)

    def __init__(self, p: Point, n: int):
        self._bonded: [Link] = []
        super().__init__(p, n)

    def canDisplace(self, o):
        if isinstance(o, (Hole, Substrate)):
            return True
        else:
            return False

    def setFree(self, b: bool):
        self._free = b

    def isFree(self):
        return len(self._bonded) == 0

    def canBond(self):
        return len(self._bonded) < 2

    def isSinglyBonded(self) -> bool:
        return len(self._bonded) == 1

    def addBond(self, l: 'Link'):
        assert self.isNeighbour(l)
        assert len(self._bonded) <= 1
        if l in self._bonded:
            # TODO: log a warning here
            return
        self._bonded.append(l)

    def removeBond(self, l: 'Link') -> bool:
        if l in self._bonded:
            self._bonded.remove(l)
            return l.removeBond(self)
        return False

    def getAllBondedLinks(self) -> ['Link']:
        return self._bonded

    def getBondedLink(self, index: int) -> 'Link':
        assert -1 < index < 2
        return self._bonded[index]

    def isBondingAngleOk(self, l: 'Link', grid: Dict[Point, Element]) -> bool:
        """Return True if resulting bonding angle will be >= 90 deg.

        This impl uses the following observation.
        1. If l is in ortho list then l1 must not be in ortho list (i.e. can be a neighbour)
        2. if l is not in ortho list then l1 must not be a neighbour

        :param l: the singly bonded neighbour to consider
        :param grid: the grid layout
        :return: True if resulting bond angle >=90 deg False otherwise
        """
        assert l.isSinglyBonded()
        l1 = l.getBondedLink(0)
        ortho_list = [grid[n] for n in self.getOrthoNeighbours()]
        n_list = [grid[n] for n in self.getNeighbours()]
        assert l in n_list
        if l in ortho_list:
            if l1 in ortho_list:
                return False
        else:
            if l1 in n_list:
                return False
        return True

    def __eq__(self, other):
        return super().__eq__(other) and self._bonded == other._bonded


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

    def doSwap(self, this: Element, other: Element):
        self.logger.debug('Swapping {0} and {1}'.format(this, other))
        temp = self.grid[this.point]
        self.grid[this.point] = other
        self.grid[other.point] = temp
        this.swap(other)

    def dobondTwo(self, l1: Link, l2: Link):
        self.logger.debug('Bonding {0} and {1}'.format(l1, l2))
        l1.addBond(l2)
        l2.addBond(l1)

    def formBond(self, target: Link, m_list: [Link], n_list: [Link]):
        def bondWithFreeL(target: Link, n_list: [Link]):
            # 6.41
            n_list_filtered = [n for n in n_list if n.isBondingAngleOk(target, self.grid)]
            # 6.42
            if not n_list_filtered:
                return
            # 6.43
            n = self.chooser.chooseOne(n_list_filtered)
            self.dobondTwo(target, n)

        # 6.2
        m_list = [m for m in m_list if target.isBondingAngleOk(m, self.grid)]
        # 6.3
        if len(m_list) >= 1:
            m1 = self.chooser.chooseOne(m_list)
            self.dobondTwo(target, m1)
            # 6.3 contd
            if len(m_list) > 1:
                # remove m1
                m_list.remove(m1)
                m2 = self.chooser.chooseOne([m for m in m_list if target.isBondingAngleOk(m, self.grid)])
                if m2 is None:
                    bondWithFreeL(target, n_list)
                    return
                else:
                    self.dobondTwo(target, m2)
                    return
        # 6.4
        bondWithFreeL(target, n_list)

    def doBond(self):
        # 6
        new_list = [l for l in self.l_list if l.isFree()]
        if not new_list:
            return
        for link in self.chooser.shuffleList(new_list):
            # 6.1
            if link.hasNeighbourOfType(Link, self.grid):
                m_list = [n for n in link.getNeighboursOfType(Link, self.grid) if n.isSinglyBonded()]
                n_list = [n for n in link.getNeighboursOfType(Link, self.grid) if n.isFree()]
                self.formBond(link, m_list, n_list)

    def doStep(self):
        self.logger.error('doStep() not implemented')

    def displaceSubstrate(self, element: T, neighbour: T):
        # 2.321
        if neighbour.hasNeighbourOfType(Hole, self.grid):
            neighbour_hole = self.chooser.chooseOne(neighbour.getNeighboursOfType(Hole, self.grid))
            self.doSwap(neighbour, neighbour_hole)
            self.doSwap(element, neighbour_hole)
        # 2.322
        elif neighbour.hasNeighbourOfType(Link, self.grid):
            links = neighbour.getNeighboursOfType(Link, self.grid)
            # remove 'this'
            links.remove(element)
            l = self.chooser.chooseOne([l for l in links if not l.isFree()])
            h = self.chooser.chooseOne([h for h in l.getNeighboursOfType(Hole, self.grid)])
            self.doSwap(neighbour, h)
            self.doSwap(element, h)
        # 2.323
        else:
            self.doSwap(element, neighbour)

    def moveLink(self, link: Link, neighbour: Element) -> bool:
        # 2.32 'S will be displaced'
        if isinstance(neighbour, Substrate):
            self.displaceSubstrate(link, neighbour)
            return True
        # 2.33
        elif isinstance(neighbour, Hole):
            self.doSwap(link, neighbour)
            return True
        # 2.31
        elif isinstance(neighbour, (Link, Catalyst)):
            # do nothing
            return False


def GridPrettyPrintHelper(grid: Dict[Point, T]) -> str:
    m = int(math.sqrt(len(grid)))
    out = []
    for j in range(m):
        for i in range(m):
            c = grid[(i, j)]
            if isinstance(c, Hole):
                out.append('H')
            elif isinstance(c, Substrate):
                out.append('S')
            elif isinstance(c, Link):
                if c.isFree():
                    out.append('o')
                elif c.isSinglyBonded():
                    out.append(chr(149))
                else:
                    out.append(chr(148))
            elif isinstance(c, Catalyst):
                out.append('K')
            out.append(' ')  # space between chars
        out.append('\n')
    return ''.join(out)


class HoleProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doStep(self):
        for hole in self.chooser.shuffleList(self.h_list):
            n = self.grid[hole.chooseNeighbour(self.chooser)]
            # 1.30
            if isinstance(n, (Substrate, Catalyst)):
                self.doSwap(hole, n)
            elif isinstance(n, Link):
                if n.isFree():
                    self.doSwap(hole, n)
                # 1.32 'L is bonded, swap with extended neighbour S'
                else:
                    s_list = [s for s in n.getNeighboursOfType(Substrate, self.grid)]
                    en_list = hole.getExtendedNeighbours()
                    # find the right extended neighbour
                    common_s = [e for e in en_list if e in s_list]
                    assert len(common_s) == 1
                    self.doSwap(hole, common_s[0])
            # 1.31
            elif isinstance(n, Hole):
                # do nothing
                pass
            # 1.4
            self.doBond()


class LinkProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doStep(self):
        free_l_list = [l for l in self.l_list if l.isFree()]
        for link in self.chooser.shuffleList(free_l_list):
            # only choose one neighbour to operate upon
            n = self.grid[link.chooseNeighbour(self.chooser)]
            # this is best effort so don't care about return type
            self.moveLink(link, n)
            # 2.4
            self.doBond()


class CatalystProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doStep(self):
        # 3.1
        for catalyst in self.chooser.shuffleList(self.k_list):
            # 3.2
            n = self.grid[catalyst.chooseNeighbour(self.chooser)]
            # 3.32 except bonding
            moved_link = False
            if (isinstance(n, Link)) and n.isFree():
                for nl in self.chooser.shuffleList(n.getNeighbours()):
                    # if L was moved then swap K and L
                    if self.moveLink(n, nl):
                        self.doSwap(catalyst, nl)
                        moved_link = True
                        break
                # 3.34
                if not moved_link:
                    self.doSwap(Catalyst, n)
            # 3.33
            elif isinstance(n, Substrate):
                self.displaceSubstrate(catalyst, n)
            # 3.35
            elif isinstance(n, Hole):
                self.doSwap(catalyst, n)
            # 3.3
            elif isinstance(n, Catalyst) or (isinstance(n, Link) and not n.isFree()):
                pass
            # moved the bonding of 3.32 and 3.34 here
            self.doBond()


class ProductionProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doStep(self):
        for catalyst in self.chooser.shuffleList(self.k_list):
            # !! Use only 1 S instead of 2 to avoid non-local effects during disintegration
            # K + S -> L + K
            # 4.1
            if catalyst.hasNeighbourOfType(Substrate, self.grid):
                # execute action with some probability
                if self.chooser.flipWeightedCoin():
                    # 4.2
                    s = self.chooser.chooseOne(catalyst.getNeighboursOfType(Substrate, self.grid))
                    l = Link.CreateLink(s.point.x, s.point.y, s.getGridSize())
                    self.grid[l.point] = l
                    del s  # delete the substrate element
        # 4.3
        self.doBond()


class DisintegrationProcess(Process):

    def __init__(self, grid: Dict[Point, Element], hole_list: List[Hole], substrate_list: List[Substrate],
                 catalyst_list: List[Catalyst], link_list: [List], choose_strategy: ChooseStrategy,
                 logger: logging.Logger):
        super().__init__(grid, hole_list, substrate_list, catalyst_list, link_list, choose_strategy, logger)

    def doRebond(self, p: Point):
        element = self.grid[p]
        # 7.1 start with singly bonded Ls
        candidate_l_list = [typing.cast(Link, e) for e in element.getNeighboursOfType(Link, self.grid) if
                            typing.cast(Link, e).isSinglyBonded()]
        free_l_list = [typing.cast(Link, e) for e in element.getNeighboursOfType(Link, self.grid) if
                       typing.cast(Link, e).isFree()]

        while candidate_l_list:
            candidate_pairs: [(Link, Link)] = itertools.combinations(candidate_l_list, 2)
            valid_pairs: [(Link, Link)] = []
            for (c0, c1) in candidate_pairs:
                if not c0.isNeighbour(c1):
                    continue
                if c0 in c1.getAllBondedLinks():
                    continue
                if not c0.isBondingAngleOk(c1, self.grid):
                    continue
                valid_pairs.append((c0, c1))
            # start forming bonds
            used_links = []
            for (l0, l1) in self.chooser.shuffleList(valid_pairs):
                if l0.canBond(l1):
                    self.dobondTwo(l0, l1)
                    used_links.append(l0)
                    used_links.append(l1)
            # 7.4
            candidate_l_list.extend(free_l_list)
            # 7.5
            candidate_l_list = [c for c in candidate_l_list if c not in used_links]

    def doStep(self):
        for link in self.chooser.shuffleList(self.l_list):
            if self.chooser.flipWeightedCoin():
                p = link.point
                for bonded in link.getAllBondedLinks():
                    # TODO: Revisit if I have to care about return type
                    # probably not since bonded is guaranteed to be in link bonded list
                    # and we assume that we formed bond correctly and put link in bonded_list of bonded
                    link.removeBond(bonded)
                # disintegrate L to S
                self.grid[p] = Substrate.createSubstrate(p, link.getGridSize())
                # destroy L
                del link
                self.doRebond(p)


class WorldModel(object):

    def __init__(self, choose_strategy):
        self.choose_strategy = choose_strategy
