#!/usr/bin/python3

import numpy as np


def pointDistanceToLine(linePoints: list[list], points: np.ndarray) -> np.ndarray:
    """
    Input:
        linePoints: list[list] two points on line [[x1, y1, z1], [x2, y2, z2]]
        points: numpy array of shape (n, 3)
    Output:
        distance: array of shape (n, 1)
    """
    if len(linePoints) != 2:
        raise Exception("list linePoints in wrong format, should be [[x1, y1, z1], [x2, y2, z2]]")
    elif (len(linePoints[0]) != 3) or (len(linePoints[1]) != 3):
        raise Exception("list linePoints in wrong format, should be [[x1, y1, z1], [x2, y2, z2]]")
    if np.shape(points)[1] != 3:
        raise Exception(f"numpy array points in wrong shape,  should be (n,1) but is {np.shape(points)}")

    basePt = np.array(linePoints[0])
    vector = np.array(linePoints[1]) - basePt
    vector = vector / vector.sum()  # normalize
    # pure implementation of d = ( || (p-a) x n || ) / ( || n || )
    distance = np.sqrt(np.sum(np.square(np.cross((points - basePt), vector)), 1))
    return distance
