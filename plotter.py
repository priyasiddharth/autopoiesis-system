"""
Copyright 2020 Siddharth Priya

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pickle
import statistics as stat

import matplotlib
import matplotlib.pyplot as plt


def loadData(f: str):
    result = {}
    with open(f, 'rb') as fin:
        result = pickle.load(fin)

    probs = set(k[0] for k in result.keys())
    weights = set(k[1] for k in result.keys())

    duration_data_list = []
    labels = []
    weight = [*result][0][1]
    for prob in sorted(probs):
        duration_data_list.append([r for r in result[prob, weight][0] if r is not 0])
        labels.append(prob)
    return result, probs, weights


def plotAgainstProb(result, probs, weights):
    # consider only one weight
    weight = [*result][0][1]
    labels = []
    duration_data_list = []
    size_data_list = []
    for prob in sorted(probs):
        duration_data_list.append([r for r in result[prob, weight][0] if r is not 0])
        size_data_list.append([r for r in result[prob, weight][1] if r is not 0])
        labels.append(prob)
    doPlot(duration_data_list, labels, title='Lifetime vs probability of disintegration', xlabel='probability of '
                                                                                                 'disintegration',
           ylabel='Lifetime', path='images/plot_lifetime_prob.png')
    doPlot(size_data_list, labels, title='Cycle size vs probability of disintegration', xlabel='probability of '
                                                                                               'disintegration',
           ylabel='Cycle size', path='images/plot_cycle_size_prob.png')


def plotAgainstWeights(result, probs, weights):
    # consider only one weight
    prob = [*result][0][0]
    labels = []
    duration_data_list = []
    size_data_list = []
    for weight in sorted(weights, key=lambda x: x[0]):
        duration_data_list.append([r for r in result[prob, weight][0] if r is not 0])
        size_data_list.append([r for r in result[prob, weight][1] if r is not 0])
        labels.append(weight[0])
    doPlot(duration_data_list, labels, title='Lifetime vs Grid configuration(H, S, K)', xlabel='Elements '
                                                                                               'configuration',
           ylabel='Lifetime', path='images/plot_lifetime_config.png')
    doPlot(size_data_list, labels, title='Cycle size vs Grid configuration(H, S, K)', xlabel='Elements configuration',
           ylabel='Cycle size', path='images/plot_cycle_size_config.png')


def doPlot(data_list, labels, title, xlabel, ylabel, path):
    matplotlib.use('agg')
    plt.boxplot(data_list, labels=[' ' for l in labels], showfliers=False)
    plt.title(title)
    plt.ylabel(ylabel)
    avgs = ['{:.2f}'.format(stat.mean(r)) for r in data_list]
    std_dev = ['{:.2f}'.format(stat.stdev(r)) for r in data_list]
    plt.table(cellText=[avgs, std_dev], loc='bottom', colLabels=labels, rowLabels=['Mean', 'Std. Dev.'])
    plt.subplots_adjust(left=0.2, bottom=0.2)
    # plt.show()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main():
    a, b, c = loadData('outputfile')
    plotAgainstProb(a, b, c)
    plotAgainstWeights(a, b, c)


if __name__ == '__main__':
    main()
