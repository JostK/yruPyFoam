#!/usr/bin/python3
import os
from yruPyFoam.readWriteFoam import readKey, writeValue, removeEntry
from yruPyFoam.geometricFunctions import pointDistanceToLine
import numpy as np
from typing import Union


def setRadialTurbulentUProfile(axis: list[list[float]], R: float, Umean: float, field: Union[str, list[str]], patch: bool = False):
    """
    Function to set U in a tube according to the 1/7 power law
    Requires the files C (postProcess -func writeCellCentres -time 0) and U to be in folder 0
    Input:
        axis: list[list[float]], of the form [[x1, y1, z1],[x2, y2, z2]], two points on the tube axis
        R: float, radius
        Umean: float, mean velocity over radius
        field: str or list[str] field to set the U profile in
        patch: bool internalField or patch
    returns:
        ---
        writes to field in U
    """
    print("******************* setInitialVelocityFrom7thPowerLaw*******************")
    nvect = np.array(axis)[1] - np.array(axis)[0]
    nvect = nvect.reshape(1, 3) / np.sum(nvect)
    if isinstance(field, str):
        field = [field]
    if patch:
        rfield = ["boundaryField/" + fd + "/value" for fd in field]
    else:
        rfield = field
    for fld in rfield:
        print(f"reading radial coordinates of cell centers of {fld}")
        gCoords = np.array(readKey(os.getcwd() + "/0/C", fld))
        radDist = pointDistanceToLine(axis, gCoords)
        axialU = 60 / 49 * Umean * (1 - radDist / R) ** (1 / 7)
        axialU = axialU.reshape(len(axialU), 1)
        UfromR = np.dot(axialU, nvect)
        writeValue(os.getcwd() + "/0/U", fld, UfromR, noExpand=True)
