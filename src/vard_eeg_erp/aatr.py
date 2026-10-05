"""AATR V7B empirical magnitude classes, independent of VARS and scalp animation."""

import numpy as np

BOUNDS = np.array([0.20373157555087362, 0.4176107284291969,
                   0.722650407163723, 1.2529173250457815])
ATTRIBUTES = ['Form', 'Panel', 'Joint expression', 'Opening', 'Colour', 'Texture']
WINDOWS = ['Early 0–200 ms', 'P300 300–500 ms', 'LPP 500–800 ms']
LEVELS = ['Minimal', 'Low', 'Moderate', 'Strong', 'Very strong']


def classify(magnitude, mean_uv, bounds=BOUNDS):
    magnitude, mean_uv = float(magnitude), float(mean_uv)
    bounds = np.asarray(bounds, dtype=float)
    if bounds.shape != (4,) or not np.isfinite(bounds).all() or not np.all(np.diff(bounds) > 0) or bounds[0] <= 0:
        raise ValueError('Batas AATR harus empat angka positif yang meningkat.')
    if not np.isfinite([magnitude, mean_uv]).all() or magnitude < 0:
        raise ValueError('|Z| harus non-negatif dan amplitudo harus finite.')
    level = int(np.searchsorted(bounds, magnitude, side='right'))
    polarity = '+' if mean_uv > 0 else '-' if mean_uv < 0 else '±'
    return f'A{level}{polarity}', LEVELS[level]


def read_summary(path):
    from scipy.io import loadmat

    data = loadmat(path, simplify_cells=True)
    bounds = np.asarray(data['Q'], dtype=float)
    magnitude = np.asarray(data['medianAbsZ'], dtype=float)
    amplitude = np.asarray(data['meanAMP'], dtype=float)
    if magnitude.shape != (6, 3) or amplitude.shape != (6, 3):
        raise ValueError('Format AATR V7B memerlukan medianAbsZ dan meanAMP berukuran 6 × 3.')
    rows = []
    for a, attribute in enumerate(ATTRIBUTES):
        for w, window in enumerate(WINDOWS):
            code, level = classify(magnitude[a, w], amplitude[a, w], bounds)
            rows.append([attribute, window, f'{magnitude[a,w]:.6f}',
                         f'{amplitude[a,w]:.6f}', code, level])
    return bounds, rows
