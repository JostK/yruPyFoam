#!/usr/bin/python3
import numpy as np

def dualMeanConvergenceTest(signal: list, nLongMean: int = 1000, nShortMean: int = 100, relTol: float = 1e-4, getConvergencePoint: bool = False) -> bool:
    """
    Function to test whether a signal is aproaching a steady state based on the difference betwen the mean values over a short and a long interval at the end of the signal.
    The aim is to establish whether the signal has been monotonically converging towards a steady state over the long interval and whether the short interval represents the steady state with some tolerance.
    This function is meant to be used to check whether a calculation can be stopped based on e.g. the convergence of the forces on an object.
    Input:
        signal:             list containing the signal
        nLongMean:          length of the long interval
        nShortMean:         length of the short interval
        relTol:             if the relative tolerance between the mean values falls below this value, the test returns True. NOTE the mean value should not be zero
        getConvergencePoint: if True the function returns the index in the signal where the the condition was first true
    Output:
        str: the name of the time directory as str
    """
    if len(signal) >= nLongMean:        
        longInterval = signal[-nLongMean:]
        shortInterval = signal[-nShortMean:]
        if abs(np.mean(longInterval) - np.mean(shortInterval))/abs(np.mean(longInterval)) <= relTol:
            # checking that the maximum oscilation amplitude in the short interval is also smaller than the tolerance
            if 0.5 * (max(longInterval) - min(longInterval))/abs(np.mean(longInterval)) <= relTol:
                ## checking monotony, max and min values have to be on the sides of the long interval
                #sideTolerance = 0.1
                #if (longInterval.index(max(longInterval)) < (nLongMean*sideTolerance)) or (longInterval.index(max(longInterval)) > (nLongMean - (nLongMean*sideTolerance))):
                    #if (longInterval.index(min(longInterval)) < (nLongMean*sideTolerance)) or (longInterval.index(min(longInterval)) > (nLongMean - (nLongMean*sideTolerance))):
                if getConvergencePoint:
                    i = nLongMean + 1
                    while dualMeanConvergenceTest(signal[:i], nLongMean, nShortMean, relTol, getConvergencePoint=False) == False:
                        i = i + 1
                    return i
                else:
                    return True
    return False
            
