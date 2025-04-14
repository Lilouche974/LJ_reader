# Voltage to Temperature Conversion

# Imports
import numpy as np
import matplotlib.pyplot as plt
from labjack import ljm

a0 = 207.313253
a1 = -126.180277
a2 = -3.928505
a3 = -0.942699
a4 = -0.215084
a5 = -0.074933
a6 = -0.016769

Zl = 0.4969960998
Zu = 1.030625219

def cheb_eq(Zv):
    """
    Calculate temperature in Kelvin from voltage using Chebyshev polynomial.
    """
    k = ((Zv-Zl)-(Zu-Zv)) / (Zu-Zl)
    temp0 =  a0 * np.cos(0*np.arccos(k))
    temp1 =  a1 * np.cos(1*np.arccos(k))
    temp2 =  a2 * np.cos(2*np.arccos(k))
    temp3 =  a3 * np.cos(3*np.arccos(k))
    temp4 =  a4 * np.cos(4*np.arccos(k))
    temp5 =  a5 * np.cos(5*np.arccos(k))
    temp6 =  a6 * np.cos(6*np.arccos(k))
    temp = temp0 + temp1 + temp2 + temp3 + temp4 + temp5 + temp6
    return temp

