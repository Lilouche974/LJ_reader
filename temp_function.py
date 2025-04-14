# Testing Chebyshev polynomial for voltage to temperature conversion

# Imports
import numpy as np

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
    Chebyshev polynomial for voltage to temperature conversion.
    """
    offset_v = 2.289562
    Zv = Zv - offset_v  # Adjust the input voltage
    k = ((Zv - Zl) - (Zu - Zv)) / (Zu - Zl)
    acos_k = np.arccos(k)
    return (
        a0 * np.cos(0 * acos_k) +
        a1 * np.cos(1 * acos_k) +
        a2 * np.cos(2 * acos_k) +
        a3 * np.cos(3 * acos_k) +
        a4 * np.cos(4 * acos_k) +
        a5 * np.cos(5 * acos_k) +
        a6 * np.cos(6 * acos_k)
    )

print(cheb_eq(2.8625))  # Example usage of the function