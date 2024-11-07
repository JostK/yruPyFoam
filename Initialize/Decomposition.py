#!/usr/bin/python3
import os
from yruPyFoam.readWriteFoam import readKey, writeValue, removeEntry
import numpy as np


def oprint(message):
    print(message)
    with open("log.manualDecomposition", "a") as log:
        log.write(str(message) + "\n\n")
    return ()


def directionalRegionDecomposition(direction: str = "z", regions: list[str] = ["innerPipe", "outerPipe"], initialRun: bool = True, debug: bool = False):
    """
    Function to produce a directional composed mesh for multi region cases. Produces a cellDist file.
    The number of subdomains is defined in the standard decomposeParDict
    Relies on the manual decomposition method of FOAM. Further information below
    input:
        direction: str, can be 'x', 'y', 'z'
        regions: list[str], list of cellZone(s)
        initialRun: bool  -> write initial cellDist file and CellCentres
        debug: bool -> perform final decomposition and write cellDist volScalarField
    returns:
        -
        produces CellDist file
    ----
    Requires both a decomposeParDict.pre containing:
        numberOfSubdomains 2;  // arbitrary, should be two to have a non uniform field while keeping it simple
        method simple;
        simpleCoeffs
        {
            n (1 1 2);
        }
    and a decomposeParDict containing:
        numberOfSubdomains 180;  // arbitrary
        method               manual;
        manualCoeffs
        {
            dataFile    "cellDist";
        }
    """
    os.system("echo '' > log.manualDecomposition")
    oprint(f"starting manual decomposition in {direction} direction for regions {regions}")
    os.system("cp -r 0.org 0")
    if not os.path.isfile("constant/C"):
        oprint("writing cell centres")
        os.system("postProcess -func writeCellCentres -time constant >> log.manualDecomposition")
    os.system("cp constant/C* 0")
    if initialRun:
        os.system("decomposePar -decomposeParDict system/decomposeParDict.pre -cellDist >> log.manualDecomposition")  # JKe TODO used to be "-no-fields" but this does not exist on ald FOAM versions. Change back once updated
        os.system("rm -r processor*")
    else:
        os.system("cp 0/Cx 0/cellDist")
        writeValue("0/cellDist", "FoamFile/object", "cellDist")
        # os.system("cp constant/cellDist 0")
    dirVals = np.array(readKey(f"./0/C{direction}", "internalField"))
    procs = int(readKey("./system/decomposeParDict", "numberOfSubdomains"))
    cellsPerProc = int(np.floor(len(dirVals) / (procs - 1)))
    oprint(f"distributing {len(dirVals)} cells in {len(regions)} regions on {procs} processors in {direction} direction")
    onProc = np.ones(np.shape(dirVals)) * 100
    dirStart = np.min(dirVals) - 1e-3
    procNr = 0
    for region in regions:
        oprint(f"working on region {region}")
        Region = np.array(readKey("./constant/polyMesh/cellZones", f"entry0/{region}")["cellLabels"])
        Divisions = int(np.floor(len(Region) / cellsPerProc))
        oprint(f"dividing region {region} in {Divisions + 1} parts")
        inRegion = np.full(np.shape(dirVals), False)
        inRegion[Region] = 1
        regionDirs = np.round(dirVals.copy(), decimals=3)
        regionDirs[np.invert(inRegion)] = -1e38
        uniqueDirs = np.sort(np.unique(regionDirs))[1:]
        remainingCells = len(regionDirs[regionDirs > -1e37])
        oprint(f"total Cells in region {remainingCells}")
        oprint(f"bounds {np.min(uniqueDirs)}  {np.max(uniqueDirs)}")
        lowLim = dirStart
        for div in range(Divisions):
            cellsPerThisProc = int(np.floor(remainingCells / max(Divisions + 1 - div, 1)))
            innerZvals = uniqueDirs[uniqueDirs > lowLim]
            upLim = np.min(innerZvals)
            cellsInProc = 0
            i = 0
            while cellsInProc < cellsPerThisProc:
                upLim = innerZvals[i]
                cellsInProc = len(regionDirs[(regionDirs >= lowLim) * (regionDirs < upLim)])
                i += 1
            onProc[(regionDirs >= lowLim) * (regionDirs < upLim)] = procNr
            remainingCells -= cellsInProc
            oprint(f"processor {procNr} cells {cellsInProc} between {lowLim} and {upLim}. Remaining cells {remainingCells}")
            procNr += 1
            lowLim = upLim
        # we put the remainder on the last processor
        onProc[(regionDirs >= lowLim)] = procNr
        oprint(f"processor {procNr} cells {len(onProc[regionDirs >= lowLim])} of region {region}")
        procNr += 1
    writeValue("0/cellDist", "FoamFile/class", "labelList")
    writeValue("0/cellDist", "FoamFile/location", '"constant"')
    writeValue("0/cellDist", "internalField", [int(x) for x in onProc.tolist()], forcePrefix=str(len(onProc)))
    removeEntry("0/cellDist", "boundaryField")
    removeEntry("0/cellDist", "dimensions")
    os.system('sed -i "s/internalField//g" 0/cellDist')
    os.system("mv 0/cellDist constant/cellDist")
    if debug:
        os.system("decomposePar -decomposeParDict system/decomposeParDict -cellDist >> log.manualDecomposition")
