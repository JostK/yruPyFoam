#!/usr/bin/python3
import sys
import os
import glob
import numpy as np
import pandas as pd
from yruPyFoam.readWriteFoam import readKey, writeValue, removeEntry

def getLatestTimeDir(casePath: str) -> str:
    """
    function to get the latest time directory in a foam case
    Input:
        casePath: absolute path to the foam case
    Output:
        str: the name of the time directory as str
    """
    lst = os.listdir(casePath)
    highest = -1e9
    for i, x in enumerate(lst):
        try:
            if float(x) > highest:
                highest = float(x)
                hindx = i
        except ValueError:
            continue
    return lst[hindx]


def __timeFromTimeDirPath(timeDirPath):
    """
    helper function to return the time as float from a time directory path.
    used by removeTimeDirs
    Input:
        timeDirPath: path to the time directory as str
    Output:
        float: the time as float
    """
    timeDirPath = timeDirPath.strip("/")
    timeDir = timeDirPath.split("/")[-1]
    return float(timeDir)

def removeTimeDirs(casePath: str, mode: str, settings="", onlyFiles=[], dryRun=False):
    """
    function to delete the time directories in a OpenFOAM case.
    this function never delets the 0 directory or directories like 0.org.
    an example application can be found in the tools folder under ConvenienceTools/cleanUpTimes
    Input:
        casePath: path to the foam case as str
        mode: mode of operation as str. So far only the folowing modes are implemented:
                    all             delete all time directories
                    allButLast      delete all but the last direcory
                    allBut          delete all but the direcories given in settings (list)
                    timeStep        delete with a given time step (i.e keep the values closest to the time step given in settings)
        settings: additional data for modes.
        onlyFiles: optionally delete only the given files from the time dirs 
        dryRun: only report, don't actually delete
    """
    # append "/" to path if needed
    casePath = casePath + "/" if not casePath.endswith("/") else casePath
    
    timeDirs = []
    # add all 0.* time dirs but not 0 or 0.org or 0.init
    zeros = ""
    for nZeros in range(0, 9):
        timeDirs = timeDirs + glob.glob(f"{casePath}0.{zeros}[1-9]*/") #Note: the "/" at the end stops glob from finding files (so only directories are found)
        zeros = zeros + "0"
        
    # add all other time dirs
    timeDirs = timeDirs + glob.glob(f"{casePath}[1-9]*/")

    # sort after applying the timeFromTimeDirPath function to all dir names
    timeDirs = sorted(timeDirs, key=__timeFromTimeDirPath)

    if len(timeDirs) == 0:
        print("no time dirs were found")
        return
    else:
        print("the following time directories were found")
        print(timeDirs)
    
    # apply modes to specify what has to be deleted
    deleteDirs = []
    if mode == "all":
        deleteDirs = timeDirs
    elif mode == "allButLast":
        deleteDirs = timeDirs[:-1]
        print(f"keeping {timeDirs[-1]}")
    elif mode == "allBut":
        #check if settings is a list
        if type(settings) != list:
            sys.exit(f"ERROR: For 'allBut' option 'settings' must be a list \n(current type of 'settings' is {type(settings)})")
        # get the real dir paths
        realSettings = []
        for dirName in settings:
            realDirName = glob.glob(f"{casePath}{dirName}/")
            if len(realDirName) != 1:
                sys.exit(f"ERROR: {dirName} found in 'settings' but does not match a time directory (or multiple matches)")
            realSettings.append(realDirName[0])
        deleteDirs = [i for i in timeDirs if i not in realSettings]
        print(f"keeping {realSettings}")
    elif mode == "timeStep":
        # check if settings is convertible to a float number
        tStep = float(settings)
        
        # convert time list to float
        times = [ __timeFromTimeDirPath(i) for i in timeDirs ]
        
        # timeDirs does not contain 0 so we have to check if it is present and start the loop there if yes
        if os.path.isdir(f"{casePath}0/"):
            keepTimes = np.arange(0,times[-1], tStep).tolist()
            times = sorted(times + [0])
            timeDirs = sorted(timeDirs + [f"{casePath}0/"], key=__timeFromTimeDirPath)
            keepDirs = [f"{casePath}0/"] # always keep 0 dir (it might be added to keepDirs again later but that is not a problem)
        else:
            keepTimes = np.arange(times[0],times[-1], tStep).tolist()
            keepDirs = []
            
        ## the last time times[-1] is never included in keepTimes, we include it if it is more than 0.5*tSTep away from the last included time
        #if abs(times[-1] - keepTimes[-1]) >= 0.5 * tStep:
            #keepTimes.append(times[-1])
        #NOTE allways keep last 
        keepTimes.append(times[-1])
        print(keepTimes)
        
        for keepTime in keepTimes:
            # find the index of the closest value in the list of time dirs
            closestKeepTimeIndex = times.index(min(times, key=lambda x: abs(keepTime - x)))
            keepDirs.append(timeDirs[closestKeepTimeIndex])
            
        print(f"keeping {keepDirs}")
        deleteDirs = [i for i in timeDirs if i not in keepDirs]
    else:
        sys.exit(f"ERROR: unknown mode: {mode}")    
    
    # delete dirs if not dryRun
    if dryRun == True:
        if onlyFiles == []:
            print("the following directories would have been deleted without dryRun")
            print(deleteDirs)
        else:
            print("the following files:")
            print(onlyFiles)
            print("...would have been deleted from the ollowing directories  without dryRun:")
            print(deleteDirs)
    else:
        for deleteDir in deleteDirs:
            if onlyFiles == []:
                os.system(f"rm -rf {deleteDir}")
            else:
                for thisFile in onlyFiles:
                    os.system(f"rm {deleteDir}{thisFile}")

def __getVolumeAverage(field: pd.DataFrame, vols: pd.DataFrame, axialDir):
    """
    function used by getRadialAverage
    Input:
        field: has format { (radialDir:vals, )axialDir:vals, field:vals}
        vols: has format { axialDir:vals, 'V':vals}
    Output:
        field: has format of input field
    """
    
    # get the name of the field to be averaged
    cWihtoZ = field.columns[1:].to_list()
    
    # create new data frame, containing the axial dir with the correct precision from vols, the cell volumes and the field data
    tempDf = pd.DataFrame()
    tempDf[axialDir] = vols[axialDir]
    tempDf["V"] = vols["V"]
    tempDf[cWihtoZ[0]] = field[cWihtoZ]
    
    # multiply field value with volume
    tempDf[cWihtoZ] = tempDf[cWihtoZ].multiply(tempDf["V"], axis="index")
    # sum up all values in each radial slice
    tempDf = tempDf.groupby([axialDir]).sum()
    # divide filed * volume sum by voume sum for each radial slice
    tempDf[cWihtoZ] = tempDf[cWihtoZ].divide(tempDf["V"], axis="index")
    return tempDf


def getRadialAverage(baseFolder: str, targetFolder: str, time: str, areas: list, fields: list, roundDigitsForAxial: int, sampleHeights: np.array, axialDir: str, radialDir: str, radialLimits: list = [-9e9, 9e9]):
    """
    compute the radial average of given fields in an OpenFOAM case.
    Usefull to get e.g. the bulk temperature in a pipe.
    Input:
        baseFolder: str. basis folder of OpenFOAM case
        targetFolder: str. folder for output files
        time: str. OpenFOAM time folder to be evaluated
        areas: list of str. internalField or names of patches to be evaluated. NOTE The patches must have a value entry, so currently they cannot be e.g. zeroGradient
        fields: list of str. names of fields to be evaluated
        roundDigitsForAxial: int. sometimes the radial coordinates have to be rounded for the averaging to work
        sampleHeights: np.array. I do not quite get what this does. it is only used for vectorFields, though
        axialDir: str. Name of the axial direction x y or z
        radialDir: str. Name of the radial direction x y or z
        radialLimits: list of float. boundaries for the averaging in radial direction. Usefull to define radial sections 
    """
    axNr = 0 if axialDir == "x" else 1 if axialDir == "y" else 2 if axialDir == "z" else 10
    radNr = 0 if radialDir == "x" else 1 if radialDir == "y" else 2 if radialDir == "z" else 10

    # loop over all areas
    for area in areas:
        
        # read cell centre coordinates and volumes from file
        if area == "internalField":
            try:
                Coords = readKey(f"{baseFolder}/0/C", "internalField", precision=16)
            except:
                warnings.warn(f"\nunknown error reading {baseFolder}/0/C \n make sure you run >> postProcess -func writeCellCentres -time 0 << before this")
                
            try:
                Vols = readKey(f"{baseFolder}/0/V", "internalField", precision=16)
            except:
                warnings.warn(f"\nunknown error reading {baseFolder}/0/V \n make sure you run >> postProcess -func writeCellVolume -time 0 << before this")
                
            radialCoord = pd.Series(i[radNr] for i in Coords)
            axialCoord = pd.Series(round(i[axNr], roundDigitsForAxial) for i in Coords)
            vols = pd.DataFrame({axialDir: axialCoord, radialDir:radialCoord, "V": pd.Series(Vols)})
        else:
            try:
                Coords = readKey(f"{baseFolder}/0/C", f"boundaryField/{area}/value", precision=16)
            except:
                warnings.warn(f"\nunknown error reading {baseFolder}/0/C")
                
            radialCoord = pd.Series(i[radNr] for i in Coords)
            axialCoord = pd.Series(round(i[axNr], roundDigitsForAxial) for i in Coords)
            vols = pd.DataFrame({axialDir: axialCoord, radialDir:radialCoord, "V": pd.Series(np.ones(len(Coords)))}) # TODO actually a scaling with the face area should be implemented here
            
        # apply the provided limits to the cell centre coordinates and volumes using boolean partitioning
        insideLimits = np.logical_and(radialCoord < radialLimits[1], radialCoord > radialLimits[0]).tolist()
        tvols = vols.loc[insideLimits].copy(deep=True)
        taxialCoord = axialCoord.loc[insideLimits]
        print(f"\n{area} has {len(tvols)} of {len(vols)} cells/faces inside the limits")
        
        # find the precision for the axial coordinates for which we get clean radial stripes (the sum of the radial coordinates is the same for all stripes)
        uniqueRads = 10
        precision = 4
        while uniqueRads > 1 and precision > 1:
            tvols[axialDir] = tvols[axialDir].round(decimals=precision)
            tmp = tvols.groupby(axialDir).sum()
            uniqueRads = tmp[radialDir].round(decimals=5).nunique()
            print(f"Precision {precision} for the axial coordinates leads to {len(tmp)} stripes. The stripes have {uniqueRads} cumulative radial coordinate/s")
            precision -= 1
        
        # loop over fields
        for _fieldN in fields:
            print(f"Reading field {_fieldN} on {area}")
            
            # read data from file
            try:
                if area == "internalField":
                    fld = readKey(f"{baseFolder}/{time}/{_fieldN}", "internalField", precision=16)
                else:
                    fld = readKey(f"{baseFolder}/{time}/{_fieldN}", f"boundaryField/{area}/value", precision=16)
            except:
                warnings.warn(f"\nunknown error with field {_fieldN}")
                
            # catch uniform field (fld is float or int) --> make list
            if isinstance(fld, float) or isinstance(fld, int):
                fld = [fld for i in range(taxialCoord.size)]
                
            # check field type
            if not isinstance(fld[0], list): # volScalarField
                
                # make data frame and apply the provided limits to the field
                fldV = pd.Series(fld)
                fldV = fldV.loc[insideLimits]
                
                # create new data frame containing only the current field
                df1 = pd.DataFrame({axialDir: taxialCoord, _fieldN: fldV})
                
                #get the volume average and and append the averaged field to the output dataframe
                if "dataFileTemp" not in vars():
                    #get the volume average and and build the output dataframe (only for the first field)
                    dataFileTemp = __getVolumeAverage(df1, tvols, axialDir)
                else:
                    
                    # overwrite field if it already exists
                    if _fieldN in dataFileTemp.columns.to_list():
                        dataFileTemp = dataFileTemp.drop(_fieldN, axis=1)
                    
                    #get the volume average and and append only the averaged field to the output dataframe
                    df1 = pd.DataFrame({axialDir: taxialCoord, _fieldN: fldV})
                    tmpRet = __getVolumeAverage(df1, tvols, axialDir)
                    dataFileTemp[_fieldN] = tmpRet[_fieldN]

            #elif isinstance(fld[0], list):  # volVectorfield
                #print("volVectorField")
                
                #fldVx = pd.Series(i[0] for i in fld)
                #fldVy = pd.Series(i[1] for i in fld)
                #fldVz = pd.Series(i[2] for i in fld)
                
                ## apply radialLimits
                #insideLimits = np.logical_and(radialCoord <= radialLimits[1], radialCoord > radialLimits[0])
                #fldVx = fldVx[insideLimits]
                #fldVy = fldVy[insideLimits]
                #fldVz = fldVz[insideLimits]
                #tvols = vols[insideLimits]
                #taxialCoord = axialCoord[insideLimits]
                #tradialCoord = radialCoord[insideLimits]

                #df1 = pd.DataFrame({radialDir: tradialCoord, axialDir: taxialCoord, f"{fieldN}x": fldVx, f"{fieldN}y": fldVy, f"{fieldN}z": fldVz})
                #zHeights = [df1[axialDir].loc[[df1[axialDir].sub(zValue).abs().values.argmin()]].iloc[0] for zValue in sampleHeights]
                #indexes = np.concatenate([df1[df1["z"] == closestZ].index.values for closestZ in zHeights]).ravel().tolist()
                #dfI = df1.loc[indexes]

                ## write data to file
                #dfI.to_csv(f"{targetFolder}/{fieldN}Profile.csv", sep="\t")
            else:
                warnings.warn(f"\narea {area} on field {_fieldN} is either not a valid Type or contains no values", UserWarning, stacklevel=2)
                
            del df1
            del fldV
            fld.clear()

        if area == "internalField":
            # write data to file
            dataFileTemp.to_csv(f"{targetFolder}/Bulk.txt", sep="\t")
            #dataFileTemp.loc[:, dataFileTemp.columns.isin(["z", "T", "p", "rho"])].to_csv(f"{targetFolder}/Bulk", sep="\t")
        else:
            # write data to file
            dataFileTemp.to_csv(f"{targetFolder}/wall_{area}.txt", sep="\t")

        del dataFileTemp
