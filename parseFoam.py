#!/usr/bin/python3
import sys
import numpy as np

def parseFoamToPy(key, value):
    if "\n" in value:  # multi line value
        if value.replace("nonuniform ", "").replace("uniform ", "").startswith("List<"):  # List
            value = value.split("\n")
            listType = value[0].split("<")[-1].split(">")[0]
            listLength = int(value[1])
            startIndex = 3
            endIndex = startIndex + listLength

            if listType == "label":  # List of int
                parsedValue = list(map(int, value[startIndex:endIndex]))

            elif listType == "scalar":  # List of float
                parsedValue = list(map(float, value[startIndex:endIndex]))  # NOTE this could also easily be done with numpy

            elif listType == "vector":  # List of vectors
                parsedValue = []
                for thisValue in value[startIndex:endIndex]:
                    thisValue = thisValue.strip("()")
                    thisValue = thisValue.split()
                    parsedValue.append(list(map(float, thisValue)))

            else:
                sys.exit("FATAL ERROR: Cannot read key " + key + " which ist of type List<" + listType + ">")

            return parsedValue

        else:
            sys.exit("FATAL ERROR: Cannot read multi-line key " + key)

    else:  # single line value
        # integer or uniform integer
        try:
            parsedValue = int(value).replace("nonuniform ", "").replace("uniform ", "")
            return parsedValue
        except:
            pass

        # float
        try:
            parsedValue = float(value.replace("nonuniform ", "").replace("uniform ", ""))
            return parsedValue
        except:
            pass

        # vector
        if value.replace("nonuniform ", "").replace("uniform ", "").startswith("(") and value.endswith(")"):
            value = value.replace("nonuniform ", "").replace("uniform ", "")
            value = value.strip("()")
            value = value.split()
            parsedValue = list(map(float, value))
            return parsedValue

        # single line list
        if value.replace("nonuniform ", "").replace("uniform ", "").startswith("List<"):  # List
            value = value.replace("nonuniform ", "").replace("uniform ", "")
            listType = value.split("<")[-1].split(">")[0]
            listLength = int(value.split()[1].split("(")[0].split("{")[0])  # NOTE single line lsits can start with smooth or curly braces

            if listLength == 0:  # empty list
                parsedValue = []
                
            elif listType == "label" or listType == "scalar":
                value = value.split("(")[-1].split("{")[-1] # NOTE single line lsits can start with smooth or curly braces
                value = value.strip(")}")
                value = value.split()
                if len(value) == 1:  # uniform list
                    parsedValue = list(map(int, value * listLength)) if listType == "label" else list(map(float, value * listLength))  # uniform list of int or float
                elif len(value) > 1: # nonuniform list
                    parsedValue = list(map(int, value)) if listType == "label" else list(map(float, value))
                else:  # zero length
                    sys.exit(f"FATAL ERROR: Value of {key} seems to be empty but is supposed to have length {listLength}")   
                    
            elif listType == "vector":
                value = value.split("(")[1:] # get rid of everything before the first opening brace
                value = [i.strip("{()} ") for i in value] # strip all remaining braces and spaces
                if len(value) == 1:  # uniform list
                    uniformVec = list(map(float, value.split()))
                    parsedValue = [uniformVec] * listLength # uniform list of equal vectors
                elif len(value) > 1: # nonuniform list
                    parsedValue = []
                    for thisValue in value:
                        if thisValue != "": # skip empty list entries
                            thisValue = thisValue.split()
                            parsedValue.append(list(map(float, thisValue)))
                else:  # zero length
                    sys.exit(f"FATAL ERROR: Value of {key} seems to be empty but is supposed to have length {listLength}")   
                    
            else:
                sys.exit("FATAL ERROR: Cannot read single line list with key " + key + " which ist of type List<" + listType + ">")
            return parsedValue

        # dimensioned entry
        # TODO

        # dimension set
        # TODO
        print("nothing has ben parsed")
        # string as last resort
        parsedValue = str(value)
        return parsedValue


def parsePyToFoam(value, forcePrefix):
    if isinstance(value, str):  # no parsing for strings (also no prefix, not even forcePrefix)
        return value
    if len(np.shape(value)) > 0:
        if np.shape(value)[0] == 3:  # uniform vector
            prefix = "uniform "
        else:  # nonuniform scalar or vector field
            listType = "vector" if np.shape(value)[-1] == 3 else "scalar"  # np.shape actually works on lists too
            prefix = f"nonuniform List<{listType}> "
    else:  # uniform scalar
        prefix = "uniform "
        value = str(value)
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, list):
        if isinstance(value[0], np.float64): # lists of np.float64 are not printed well, transform to np.array and back to list for propper print
            value = np.array(value).tolist()
        value = str(value)
        value = value.replace("[", "( ")
        value = value.replace("]", " )")
        value = value.replace(",", "")
    if forcePrefix is not None:
        prefix = forcePrefix
    return prefix + value
