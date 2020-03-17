import world_model as world


class WorldViewer(object):

    def __init__(self):
        pass

    def updateView(self, grid: [world.Point, world.T]):
        pass


class ConsoleViewer(WorldViewer):

    def updateView(self, grid: [world.Point, world.T]):
        print(world.GridPrettyPrintHelper(grid))

    def __init__(self):
        pass
