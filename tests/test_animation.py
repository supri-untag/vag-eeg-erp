import numpy as np
import pytest

from vard_eeg_erp.brain3d import brain_mesh, spatial_weights


def test_mesh_and_weights_preserve_constant_potential(result):
    vertices, faces = brain_mesh()
    assert np.isfinite(vertices).all()
    assert faces.min() == 0 and faces.max() < len(vertices)
    weights, directions = spatial_weights(
        vertices, [ch["loc"][:3] for ch in result.evoked.info["chs"]]
    )
    np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-6)
    np.testing.assert_allclose(weights @ np.full(len(directions), 2.5), 2.5, atol=1e-6)


def test_missing_positions_rejected():
    with pytest.raises(ValueError, match="Posisi"):
        spatial_weights(brain_mesh()[0], np.zeros((32, 3)))
