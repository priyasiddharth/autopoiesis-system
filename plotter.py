import pickle

import matplotlib
import matplotlib.pyplot as plt


def loadData(f: str):
    result = {}
    with open(f, 'rb') as fin:
        result = pickle.load(fin)

    prob = [*result][0][0]  # the first weight
    weights = set(k[1] for k in result.keys())
    duration_data_list = []
    labels = []
    for weight in sorted(weights, key=lambda x: x[0]):
        # 0 contains duration data
        duration_data_list.append([r for r in result[prob, weight][0] if r is not 0])
        labels.append(weight)
    return duration_data_list, labels
    # TODO: check if dict empty
    # prob
    # probs = [k[0] for k in result.keys()]
    # # weights
    # weights = [k[1] for k in result.keys()]
    # prob_arr = numpy.asarray(probs)
    # holes_arr = numpy.asarray([i[0] for i in weights])
    # duration_array = numpy.empty(shape=(1, 0))
    # for p, k in zip(probs, weights):
    #     durations, sizes = result[p, k]
    #     d = statistics.mean(durations)
    #     duration_array = numpy.append(duration_array, d)
    # return prob_arr, holes_arr, duration_array


def doPlot(data_list, labels):
    matplotlib.use('Agg')
    labels = [l[0] for l in labels]
    plt.boxplot(data_list, labels=labels)
    plt.title('Lifetime vs Number of Holes')
    plt.xlabel('Number of Holes')
    plt.ylabel('Lifetime')
    # plt.scatter(prob_arr, holes_arr, s=duration_normalized, c=colors, alpha=0.5)
    plt.savefig('plot.png')


def main():
    a, b = loadData('outputfile')
    doPlot(a, b)


if __name__ == '__main__':
    main()
