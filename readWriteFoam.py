#!/usr/bin/python3

from subprocess import PIPE, run
from yruPyFoam.parseFoam import parseFoamToPy, parsePyToFoam
import sys
from typing import Any
import pandas as pd


def _warning(inp: str):
    print(f"\33[93mWARNING: {inp}\033[0m")


def __stdoutToList(stdout):
    stdout = stdout.strip("\n")
    stdout = stdout.split("\n")
    return stdout


def __readValue(thisFile, key, additionalArgs):
    """
    Wrapper function around the foamDictionary function to read values from foam dictionary
    Input:
        thisfile: str Dictionary path from current working directory
        key: str e.g. internalField or bnd1/gradient
    Output:
        dictionary or list
    """
    output = run(["foamDictionary", thisFile, "-entry", key, "-value"] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if output.returncode == 0:
        return parseFoamToPy(key.split("/")[-1], output.stdout.strip("\n"))
    else:
        sys.exit("FATAL ERROR: value of key " + key + " could not be read \n" + output.stderr)


def readKey(thisFile, key="", noExpand=False, precision=16):
    """
    Wrapper function around the foamDictionary function to read values from foam dictionary
    Input:
        thisFile: str Dictionary path from current working directory
        key: str e.g. internalField or bnd1/gradient
        noExpand: bool  wheter to run #include or #eval statements
        precision: int precision of output
    Output:
        dictionary or list
    """
    additionalArgs = ["-precision", str(precision)]
    if noExpand is True:  # include statements and other function entries can be avoided with this option but it might lead to problems in parsing the entries. NOTE cwd must typically be the top directory of the case for #include statements to work correctly
        additionalArgs.append("-disableFunctionEntries")

    outDict = {}

    # check if key has subkeys
    if key == "":
        output = run(["foamDictionary", thisFile, "-keywords"] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    else:
        output = run(["foamDictionary", thisFile, "-entry", key, "-keywords"] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    if output.returncode == 0:  # key has subkeys
        for subKey in __stdoutToList(output.stdout):
            if not subKey.startswith("#include"):  # skip all include statements unless tey are given as initial key (which would be weird)
                if key == "":
                    newKey = subKey
                else:
                    newKey = key + "/" + subKey
                # print(newKey)  #NOTE uncomment for debugging
                outDict[subKey] = readKey(thisFile, newKey)
        return outDict
    else:  # key has no subkeys
        return __readValue(thisFile, key, additionalArgs)


def writeValue(thisFile: str, key: str, value: Any, forcePrefix: str = None, noExpand: bool = False, precision: int = 16, **kwargs) -> None:
    """
    Function to write 'value' on the region 'key' in 'thisFile'.

    Input:
        thisFile: str, absolute or relative path to file
        key: str, name of field or variable to set
        value: Any, can be of arbitrary type, tested: str, int, float, np.ndarray, list
        forcePrefix: str, if set it will overwrite the defaultly generated prefix, ignored if value is of type str
        noExpand: bool, wheter to excecute function entries in file, allways enabled for large files by now
        precision: int, maximal write precision of value
    Output:
        ---
        writes to 'thisFile'
    """
    if len(kwargs) > 0:
        _warning(f"found unsupported kwargs {kwargs.keys()} in function writeValue of package yruPyFoam.readWriteFoam \nvalid keywords are ['thisFile', 'key', 'value', 'forcePrefix', 'noExpand', 'precision']")

    additionalArgs = ["-precision", str(precision)]
    if noExpand is True:
        additionalArgs.append("-disableFunctionEntries")
    parsedValue = parsePyToFoam(value, forcePrefix)
    if len(parsedValue) > 1e5:
        with open("writeValueTempfile.txt", "w") as f1:
            f1.write(parsedValue + ";")
            f1.close()
        parsedValue = '#include "./writeValueTempfile.txt"'
        if "-disableFunctionEntries" in additionalArgs:
            print("'noExpand' was set but function entries where executed anyway due to the length of the set field")
            additionalArgs.pop(additionalArgs.index("-disableFunctionEntries"))
    # we do not know if the key allready exists. try -set first, if it fails try -add
    output = run(["foamDictionary", thisFile, "-entry", key, "-set", parsedValue] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    if output.returncode != 0:
        # I think "-add" allways works, even if the entry is present allready (may through a warning)
        output = run(["foamDictionary", thisFile, "-entry", key, "-add", parsedValue] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        if output.returncode != 0:
            # falied. through error
            sys.exit("FATAL ERROR: value of key " + key + " could not be set \n" + output.stderr)
    run(["rm", "writeValueTempfile.txt"], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    print(f"sucessfully set {key} on field {thisFile}")


def removeEntry(thisFile, key, noExpand=False, precision=16):
    """
    Function to delete entry 'key' from 'thisFile'.

    Input:
        thisFile: str, absolute or relative path to file
        key: str, name of field or variable to delete
        noExpand: bool, wheter to excecute function entries in file, allways enabled for large files by now
        precision: int, maximal write precision of value
    Output:
        ---
    """
    additionalArgs = ["-precision", str(precision)]
    if noExpand is True:
        additionalArgs.append("-disableFunctionEntries")

    output = run(["foamDictionary", thisFile, "-entry", key, "-remove"] + additionalArgs, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    if output.returncode != 0:
        # still falied. through error
        sys.exit("FATAL ERROR: key " + key + " could not be deleted \n" + output.stderr)


def readPostProcessingFile(filePath: str, headerLineIndex: int = -1) -> pd.DataFrame:
    """
    function to read typical OpenFOAM post processing files (e.g. output of forces functionObject) to a pandas data frame.
    Input:
        filePath:   path to the post processing file
        headerLineIndex: (optional) specify the line index of the header 
    Output:
        pd.DataFrame: data frame containing the file content
    """
    with open(filePath) as f : 
        lines = f.readlines()
        # search header if it is not specified
        if headerLineIndex == -1: 
            headerLineIndex = 0
            while lines[headerLineIndex].startswith("#"):
                headerLineIndex += 1
            headerLineIndex -= 1
        # remove the leading '#' from the header
        header = lines[headerLineIndex].strip().split()[1:]
    
    # read the file to pandas
    data = pd.read_csv(filePath, sep="\s+", skiprows=headerLineIndex+1, header=None, names=header, skipinitialspace=True) 
    
    # TODO files and even the header may contain vectors and columns may have duplicate names
    return data

# *********** Some comments *************
# If a full key is given e.g. like this:
# value = readKey("./0/U", "boundaryField/Inlet/value")
# the function returns a value (could be a single value or a list of values or a keyword).
#
# If no key or the key of a subdict is given e.g. like this:
# value = readKey("./0/U")
# or this
# value = readKey("./0/U", "boundaryField/Inlet")
# the function returns a dictionary which is structured like the foam file
#
# Typically, the cwd must be the top directory of the case to use this fuction or #include statements wont work.
# Include statemetns can be switched of with the "noExpand" switch, but this may lead to problems in parsing entries like "value uniform (0 0 $Uinlet);"
#
# TODO
# for writing entire dictionarys it would probably be easies to first replace the existing dict/subdict (if it exists) with an empty one
# foamDictionary 0/U -entry boundaryField/Inlet -set '{}'
# and then fill it with single values, like this:
# foamDictionary 0/U -entry boundaryField/Inlet/type -add 'fixedValue'
# Note that foamDictionary could also (alternatively) take entire dicts/subdicts like this:
# foamDictionary 0/T -entry boundaryField/Inlet -set '{type fixedValue; value nonuniform List<scalar> 3 (1 2 3 );}'
# but this would probably be trickyer to parse.
# Note that we do not need to worry about line breaks. foamDictionary takes care of that.
