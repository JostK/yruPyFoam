#!/usr/bin/python3
import numpy as np
from scipy.optimize import fsolve

def yPlusCalculator(yplusDes, U, rho, nu, L, CfFunction = None):
    """
    function to calculate the wall cell thickness for a desired yPlus depending on freestream velocity, BL length and fluid properties
    input:
        yPlusDes:   desired yPlus value [-]
        U:          freestream velocity [m/s]
        rho:        density [Kg/m3]
        nu:         kinematic viscosity []
        L:          Boundary layer thickness [m]
        CfFunction: Optional function handle for Cf (must be a function of Re). Note, for pipes a fanning friction factor (1/4 * Darcy) has to be given
    output:
        Re:         ReynoldsNumber
        yP:         Cell centroid wall distance for first cell [m]    
    """
    Re = U*L/nu
    # use standard friction line for Cf if no special function is given
    if CfFunction is None:
        Cf = np.power(2*np.log10(Re)-0.65, -2.3) # valid for Re<1e9
    else:
        Cf = CfFunction(Re)
    tau_wByRho = Cf * 0.5 * U**2
    ustar=np.sqrt(tau_wByRho)
    yP=yplusDes*nu/ustar
    return [Re, yP]

def findGrowRateFirst(distG, firstCell, N, guess=1.1, precision=4):
    """
    function to get growth rate based on given number of cells, maximum size of first cell and general distance
    input:
        distG:        general distance
        firstCell:    maximum size of first cell
        N:            number of cells
        guess:        initial guess for cell-to-cell grow rate
        precision:    output precision    
    output:
        growRate:    cell-to-cell grow rate
        resFCell:    resulting size of first cell
        resLCell:    resulting size of last cell
    _____
    distG = sum_{n=0}^{N-1} firstCell*growRate^n => distG/firstCell =  sum_{n=0}^{N-1} growRate^n = (1 - growRate^N) / (1-growRate)
    """
    func = lambda gR : (1 -gR**N) / (1 - gR) * firstCell - distG     
    [growRate] = fsolve(func, guess)
    #as it will be entered with a limited precision, the result will be rounded
    growRate = np.ceil(growRate*10**precision)/(10**precision)
    # resulting size of first cell
    resFCell = distG / ((1-growRate**N)/(1-growRate))
    resLCell = resFCell*growRate**(N-1)
    return [growRate, resFCell, resLCell]

def findGrowRateLast(distG, lastCell, N, guess=1.1, precision=4):
    """
    function to get growth rate based on given number of cells, maximum size of wall cell and general distance
    input:
        distG:        general distance
        lastCell:    maximum size of wall nearest cell
        N:            number of cells in wall normal direction
        guess:        initial guess for cell-to-cell grow rate
        precision:    output precision    
    output:
        growRate:    cell-to-cell grow rate
        resFCell:    resulting size of first cell
        resLCell:    resulting size of last cell
    _____
    distG = sum_{n=0}^{N-1} firstCell*growRate^n => distG/firstCell =  sum_{n=0}^{N-1} growRate^n = (1 - growRate^N) / (1-growRate)
    """
    func = lambda gR : (1 -gR**N) / (1 - gR) * lastCell/(gR**(N-1)) - distG     
    [growRate] = fsolve(func, guess)
    #as it will be entered with a limited precision, the result will be rounded
    growRate = np.ceil(growRate*10**precision)/(10**precision)
    # resulting size of first cell
    resFCell = distG / ((1-growRate**N)/(1-growRate))
    resLCell = resFCell*growRate**(N-1)
    return [growRate, resFCell, resLCell]

def findCellNumberFirst(distG, firstCell, growRate):
    """
    function to get Number of cells based on grow rate, maximum size of wall cell and general distance
    input:
        distG:        general distance
        firstCell:    maximum size of wall nearest cell
        growRate:     cell-to-cell grow rate    
    output:
        N:            Number of cells
        resFCell:     resulting size of first cell
        resLCell:     resulting size of last cell
    """
    #if growRate<1.0: raise ValueError("please provide grow rate >1")
    #guess=(distG/firstCell)/growRate**(distG/firstCell)
    func = lambda N : (1 -growRate**N) / (1 - growRate) - distG / firstCell    
    [N] = fsolve(func, 100)
    #as a full number of cells is needed and firstCell represents a maximum distance, the number is rounded up
    N = np.ceil(N)
    # resulting size of first cell
    resFCell = distG / ((1-growRate**N)/(1-growRate))
    resLCell = resFCell*growRate**(N-1)
    return [N, resFCell, resLCell]

def findCellNumberFirstLast(distG, firstCell, lastCell):
    """
    function to get Number of cells based on size of first and last cell, and general distance
    input:
        distG:        general distance
        firstCell:    maximum size of wall nearest cell
        lastCell:     size of last cell    
    output:
        N:            Number of cells
        resFCell:     resulting size of first cell
        resLCell:     resulting size of last cell
    """
    #if growRate<1.0: raise ValueError("please provide grow rate >1")
    #guess=(distG/firstCell)/growRate**(distG/firstCell)
    func = lambda N : firstCell * ((1-(lastCell/firstCell)**(N/(N-1.0)))/(1-((lastCell/firstCell)**(1.0/(N-1.0))))) - distG 
    [N] = fsolve(func, 100)
    #as a full number of cells is needed and firstCell represents a maximum distance, the number is rounded up
    N = np.ceil(N)
    # resulting size of first cell
    growRate = (lastCell/firstCell)**(1.0/(N-1.0))
    resFCell = distG / ((1-growRate**N)/(1-growRate))
    resLCell = resFCell*growRate**(N-1)
    return [N, resFCell, resLCell, growRate]

def gradingCalculator(firstCell=None, lastCell=None, nCells=None, distance=None, growRate=None):
    """
    function to calculate grading information from variable inputs. Not all inputs have to be given and the idea is that the function will calculate the other other (not provided) parameters. Not all functions are implemented yet.
    input:
        firstCell:    size of first cell
        lastCell:     size of last cell
        nCells:       number of cells
        distance:     overall distance 
        growRate:     cell-to-cell grow rate
    output:
        firstCell:    size of first cell
        lastCell:     size of last cell
        nCells:       number of cells
        distance:     overall distance 
        growRate:     cell-to-cell grow rate
    _____
    distG = sum_{n=0}^{N-1} firstCell*growRate^n => distG/firstCell =  sum_{n=0}^{N-1} growRate^n = (1 - growRate^N) / (1-growRate)
    """
    
    #print(f"Grading calculation with firstCell = {firstCell}, lastCell = {lastCell}, nCells = {nCells}, distance = {distance}, growRate = {growRate}")
    
    if (distance is not None) and (firstCell is not None) and (nCells is not None):
        guess= (distance / nCells) / firstCell # if the first cell is larger than the mean cell, the grading is likely < 1 and vice versa.
        precision=4
        growRate, firstCell, lastCell = findGrowRateFirst(distance, firstCell, nCells, guess, precision)
    elif (distance is not None) and (lastCell is not None) and (nCells is not None):
        guess= lastCell / (distance / nCells) # if the first cell is larger than the mean cell, the grading is likely < 1 and vice versa.
        precision=4
        growRate, firstCell, lastCell = findGrowRateLast(distance, lastCell, nCells, guess, precision)
    elif (distance is not None) and (firstCell is not None) and (growRate is not None):
        nCells, firstCell, lastCell = findCellNumberFirst(distance, firstCell, growRate)
    elif (firstCell is not None) and (lastCell is not None) and (nCells is not None):
        growRate = (lastCell/firstCell)**(1.0/(nCells-1.0))
        distance = firstCell * ((1-growRate**nCells)/(1-growRate))
    elif (firstCell is not None) and (lastCell is not None) and (growRate is not None):
        nCells = np.log(lastCell/firstCell) / np.log(growRate) + 1
        distance = firstCell * ((1-growRate**nCells)/(1-growRate))       
    elif (firstCell is not None) and (lastCell is not None) and (distance is not None):
        nCells, firstCell, lastCell, growRate = findCellNumberFirstLast(distance, firstCell, lastCell)
    else:
        raise KeyError(f"Grading calculation with firstCell = {firstCell}, lastCell = {lastCell}, nCells = {nCells}, distance = {distance}, growRate = {growRate} is not (yet) implemented")
    return [firstCell, lastCell, nCells, distance, growRate]
        
