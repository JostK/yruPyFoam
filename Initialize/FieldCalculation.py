#!/usr/bin/python3
import os
from yruPyFoam.readWriteFoam import readKey, writeValue, removeEntry
import numpy as np


def omegaFromKEpsilon(dir: str, regions: list[str]) -> None:
    """
    """
    for region in regions:
        if not region == "internalField":
            appdx = "/value"
            region = f"boundaryField/{region}/value"
        else:
            appdx = ""
        kfield = np.array(readKey(f"{dir}/k", region, noExpand=True))
        efield = np.array(readKey(f"{dir}/epsilon", region, noExpand=True))
        omegaField = efield / (0.09 * kfield)
        writeValue(f"{dir}/omega", region, omegaField)
    return None
