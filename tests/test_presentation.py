import numpy as np
import pytest

from vard_eeg_erp.presentation import WINDOWS, component_values


def test_component_means_use_same_erp(result):
    values = component_values(result)
    for index, (_, start, end) in enumerate(WINDOWS):
        mask = (result.evoked.times * 1000 >= start) & (result.evoked.times * 1000 <= end)
        np.testing.assert_allclose(values[index], result.evoked.data[:, mask].mean(axis=1) * 1e6)


def test_window_outside_epoch_rejected(result):
    from dataclasses import replace

    cropped = replace(result, evoked=result.evoked.copy().crop(tmax=0.5))
    with pytest.raises(ValueError, match="LPP"):
        component_values(cropped)
