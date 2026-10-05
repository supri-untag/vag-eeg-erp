import numpy as np
import pytest

from vard_eeg_erp.aatr import BOUNDS, classify
from vard_eeg_erp.brain3d import activity_colors


def test_aatr_boundaries_and_polarity():
    assert classify(0, 0)[0] == 'A0±'
    for index, bound in enumerate(BOUNDS):
        assert classify(np.nextafter(bound, 0), 1)[0] == f'A{index}+'
        assert classify(bound, -1)[0] == f'A{index + 1}-'
    assert classify(.884525701519766, .444373096182454)[0] == 'A3+'
    assert classify(1.08227042276664, -.20903411441475)[0] == 'A3-'


@pytest.mark.parametrize('value', [-1, np.nan, np.inf])
def test_invalid_magnitude(value):
    with pytest.raises(ValueError):
        classify(value, 1)


def test_glow_preserves_zero_and_signed_magnitude():
    colors = activity_colors(np.array([-2., 0., 2.]), 4)
    assert colors[1, 3] == 0
    assert colors[0, 3] == colors[2, 3]
    assert colors[0, 0] > colors[2, 0]
    assert colors[0, 1] < colors[2, 1]
