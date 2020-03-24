import itertools
import logging
import os
import pickle
import statistics
from typing import Dict

import helper
import world_model as world
import world_viewer as viewer


class WorldPresenter(object):

    def __init__(self, viewer: viewer.WorldViewer, context: world.WorldContext,
                 experiment: helper.Experiment):
        self._ctx = context
        self._viewer = viewer
        self._iter = 0
        self._hole_process: world.HoleProcess = self._ctx.hole_process
        self._link_process: world.LinkProcess = self._ctx.link_process
        self._catalyst_process: world.CatalystProcess = self._ctx.catalyst_process
        self._prod_process: world.ProductionProcess = self._ctx.production_process
        self._disintegrate_process: world.DisintegrationProcess = self._ctx.disintegration_process
        self._cycle_observer: world.CycleObserver = self._ctx.cycle_observer
        self._grid: Dict[world.Point: world.T] = self._ctx.grid
        self._iter: int = self._ctx.max_iter
        self._born_iter = 0
        self._cycle_maintained = False
        self._cycle_length = 0
        self._experiment: helper.Experiment = experiment

    def _doSingleStep(self):
        self._hole_process.doStep()
        self._link_process.doStep()
        self._catalyst_process.doStep()
        self._prod_process.doStep()
        self._disintegrate_process.doStep()

    def postProcessAndContinue(self, iteration: int) -> bool:
        cycle_found, cycle_broken, cycle_length = self._cycle_observer.doStep()
        if cycle_found and not cycle_broken:
            if not self._cycle_maintained:
                self._cycle_maintained = True
                self._born_iter = iteration
            # store the latest cycle length before breaking
            self._cycle_length = cycle_length
            logging.getLogger('presenter:').info('Cycle found at iteration:{'
                                                 '0}'.format(iteration))
        elif cycle_found and cycle_broken:
            self._cycle_maintained = False
            self._experiment.addRecord(self._born_iter, iteration,
                                       self._cycle_length)
            logging.getLogger('presenter:').info('Cycle broke at iteration:{'
                                                 '0}'.format(iteration))
            return False
        return True

    def doSimulate(self):
        self._viewer.updateView(self._grid, iteration=0)
        for i in range(self._iter):
            self._doSingleStep()
            self._viewer.updateView(self._grid, i)
            self.postProcessAndContinue(i)


class ConsolePresenter(WorldPresenter):

    def __init__(self, viewer: viewer.ConsoleViewer, config: helper.Config,
                 exp: helper.Experiment
                 ) -> None:
        super().__init__(viewer, config, exp)


def batch_run():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))
    grid_size = 10
    iter = 100
    view = viewer.NullViewer()
    grid_seeds = range(0, 10)
    proc_seeds = range(100, 110)
    disint_prbs = [0.1]
    # H S K
    weights_list = [[9 + i, 90 - i, 1] for i in range(0, 90, 5)]
    result = {}
    factory = world.WorldFactory()
    for grid_seed, proc_seed, disint_prb, weights in itertools.product(grid_seeds, proc_seeds, disint_prbs,
                                                                       weights_list):
        exp = helper.AliveDurationExperiment()
        ctx: world.WorldContext = factory.createRandomWorld(grid_size, weights, grid_random_seed=grid_seed,
                                                            max_iter=iter,
                                                            proc_random_seed=proc_seed,
                                                            disintegrate_prob=disint_prb)
        wp = WorldPresenter(view, ctx, exp)
        wp.doSimulate()
        result[(grid_seed, proc_seed, disint_prb, tuple(weights))] = exp.process() if exp.process() else [[0, 0]]

    result_dict = {}
    display_dict = {}
    for prob, weights in itertools.product(disint_prbs, weights_list):
        alive_stats = []
        size_stats = []
        for grid_seed, proc_seed in itertools.product(grid_seeds, proc_seeds):
            alive_stats.extend([i[0] for i in result[grid_seed, proc_seed, prob, tuple(weights)]])
            size_stats.extend([i[1] for i in result[grid_seed, proc_seed, prob, tuple(weights)]])
        result_dict[prob, tuple(weights)] = (alive_stats, size_stats)
        display_dict[prob, tuple(weights)] = ((alive_stats), statistics.mean(size_stats))
    print(display_dict)
    with open('outputfile', 'wb') as fout:
        pickle.dump(result_dict, fout)

def main():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
    path = 'config.json'
    view = viewer.ConsoleViewer()
    exp = helper.AliveDurationExperiment()
    config: helper.Config = helper.Config.loadConfigFromFile(path)
    presenter = ConsolePresenter(view, config, exp)
    presenter.doSimulate()
    print(exp.alive_durations)
    print(exp.process())


if __name__ == '__main__':
    batch_run()
