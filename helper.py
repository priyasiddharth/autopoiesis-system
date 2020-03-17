from world_model import *


def FindCycle(link: 'Link', visited: ['Link']) -> List['Link']:
    if link.isFree():
        assert False
    if link.isSinglyBonded():
        return []
    if len(link.getAllBondedLinks()) == 2:
        if not link.getBondedLink(0) in visited:
            r = FindCycle(link.getBondedLink(0), visited + [link])
        elif not link.getBondedLink(1) in visited:
            r = FindCycle(link.getBondedLink(1), visited + [link])
        else:
            return [link]
        if not r:
            return []
        else:
            return [link] + r
