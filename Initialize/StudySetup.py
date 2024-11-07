#!/usr/bin/python3
import os
import numpy as np


def reorderStudyParameterSpace(mainParameter: list, *args: list, nNodes=1) -> int:
    """
    Function to reorder a set of parameters to get visible results as fast as possible
    input:
        mainParameter: list  parameter that defines the ordering space
        *args: (multiple) list(s)  additional parameters that will be ordered according to the main parameter
    output:
        lst: list shape: [nNodes] [len(args)+1] [~len(mainParameter)/nNodes]
    """
    plen = len(mainParameter)
    for i, arg in enumerate(args):
        if not plen == len(arg):
            raise Exception(f"additional argument in position {i} has not the same length as the main parameter")
    elmPos = np.arange(0, plen)
    elmOrder = np.zeros(plen)
    elmSet = np.array(np.zeros(plen), dtype=bool)
    # firstly we will evaluate points on 0.25, 0.5 and 0.75 of the array
    for n, i in enumerate([int(np.floor(p * (plen - 1))) for p in [0, 0.33, 0.66, 1]]):
        elmOrder[i] = n
        elmSet[i] = True

    count = 4
    while np.sum(elmSet.astype(int)) < plen:
        diff = np.diff(elmPos[elmSet])
        rind = np.argmax(diff) + 1
        ind = elmPos[elmSet]
        ind = ind[rind] - np.floor(np.max(diff) / 2).astype(int)
        elmOrder[ind] = count
        elmSet[ind] = True
        count += 1
    newMainParameter = np.array(sorted(list(zip(elmOrder, mainParameter)), key=lambda x: x[0]), dtype=type(mainParameter[0]))[:, 1].tolist()
    nargs = list(args)
    for i, arg in enumerate(args):
        nargs[i] = np.array(sorted(list(zip(elmOrder, arg)), key=lambda x: x[0]), dtype=type(arg[0]))[:, 1].tolist()

    lst = np.empty((nNodes, 1 + len(args))).tolist()
    for node in range(nNodes):
        lst[node][0] = newMainParameter[node::nNodes]
        for i, narg in enumerate(nargs):
            lst[node][i + 1] = narg[node::nNodes]

    return lst


# 0.00050000, 0.00062962, 0.00079284, 0.00099837,
# 0.026594, 0.026594, 0.026594, 0.026594,
hflx = [0.00125718, 0.00158308, 0.00199347, 0.00251024, 0.00316099, 0.00398042, 0.00501228, 0.00631164, 0.00794783, 0.01000818, 0.01260265, 0.01586968, 0.01998365, 0.02516410, 0.03168750, 0.03990198, 0.05024595, 0.06327142, 0.07967354, 0.10032766, 0.12633603, 0.15908667, 0.20032739, 0.25225913, 0.31765335, 0.40000000]
velc = [0.026594, 0.026594, 0.026593, 0.026593, 0.026593, 0.026593, 0.026593, 0.026592, 0.026592, 0.026592, 0.026591, 0.02659, 0.026589, 0.026588, 0.026587, 0.026585, 0.026582, 0.026579, 0.026575, 0.026571, 0.026565, 0.026557, 0.026547, 0.026535, 0.02652, 0.026501]

a, b = reorderStudyParameterSpace(hflx, velc, nNodes=2)
print(a)
print(b)
