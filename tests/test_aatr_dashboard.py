import numpy as np
import pytest
from scipy.io import savemat

from vard_eeg_erp.aatr_dashboard import read_figure, render_figure


def test_non_figure_rejected(tmp_path):
    path = tmp_path / 'summary.mat'
    savemat(path, {'meanAMP': np.zeros((6, 3))})
    with pytest.raises(ValueError, match='FIG'):
        read_figure(path)


def test_incomplete_dashboard_rejected(tmp_path):
    path = tmp_path / 'incomplete.fig'
    savemat(path, {'hgS_070000': {'children': {'type': 'axes'}}})
    with pytest.raises(ValueError, match='6 panel'):
        read_figure(path)


def test_render_preserves_signed_curve_and_export(tmp_path):
    x, y = np.array([0., 100., 200.]), np.array([-.7, 0., .9])
    axis = {'type': 'axes', 'properties': {
        'Position': [.1, .2, .4, .5], 'XLim': [0, 200], 'YLim': [-1, 1]},
        'children': [{'type': 'graph2d.lineseries', 'properties': {'XData': x, 'YData': y}}]}
    figure = render_figure({'children': [axis]})
    np.testing.assert_array_equal(figure.axes[0].lines[0].get_ydata(), y)
    np.testing.assert_array_equal(figure.axes[0].lines[0].get_xdata(), x)
    for extension in ('png', 'pdf'):
        path = tmp_path / f'dashboard.{extension}'
        figure.savefig(path)
        assert path.stat().st_size > 100
