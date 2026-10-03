import time

import pytest
from PySide6.QtTest import QTest

from vard_eeg_erp.app import MainWindow, create_application


@pytest.fixture(scope="module")
def app():
    return create_application()


def test_linked_cursor_and_invalidation(app, recording, result):
    window = MainWindow(auto_demo=False)
    window.install_recording(recording)
    window.install_result(result)
    window.select_time(400)
    sample = result.sample(400)
    assert window.slider.value() == sample
    assert window.erp_plot.getAxis("bottom").autoSIPrefix is False
    assert window.erp_plot.cursor.value() == result.evoked.times[sample] * 1000
    assert float(window.channel_table.item(0, 1).text()) == pytest.approx(
        result.evoked.data[0, sample] * 1e6, abs=0.00051
    )
    window._render_topomap()
    assert len(window.topomap.figure.axes) == 2
    window.events.setCurrentText("Visual B")
    assert window.result is None
    assert not window.export_button.isEnabled()
    assert window.channel_table.rowCount() == 0
    window.dirty = False
    window.close()


def test_background_demo_completes(app):
    window = MainWindow(auto_demo=False)
    errors = []
    window.show_error = errors.append
    window.load_demo()
    deadline = time.monotonic() + 30
    while window.job is not None and time.monotonic() < deadline:
        QTest.qWait(25)
    assert window.job is None
    assert not errors
    assert window.result.accepted == 12
    assert window.run_button.isEnabled()
    window.dirty = False
    window.close()


def test_presentation_playback_and_reset(app, recording, result):
    from vard_eeg_erp.analysis import Settings, analyze

    window = MainWindow(auto_demo=False)
    window.install_recording(recording)
    other = analyze(recording, Settings(), "Visual B")
    window.presentation.set_results([result, other])
    window.navigate(4)
    while len(window.presentation.cache) < len(window.presentation.results):
        QTest.qWait(20)
    window.presentation.toggle()
    assert window.presentation.timer.isActive()
    window.presentation.advance()
    assert window.presentation.slider.value() == 1500
    assert "Visual B" in window.presentation.title.text()
    assert len(window.presentation.figure.axes) == 6
    window.presentation.advance()
    assert not window.presentation.timer.isActive()
    window.invalidate_result()
    assert not window.presentation.results
    assert not window.presentation.play.isEnabled()
    window.dirty = False
    window.close()


def test_3d_timeline_and_invalidation_without_opengl(app, recording, result):
    window = MainWindow(auto_demo=False)
    window.install_recording(recording)
    window.install_result(result)
    window.brain.seek(100)
    assert window.sample_index == 100
    assert window.slider.value() == 100
    assert window.erp_plot.cursor.value() == result.evoked.times[100] * 1000
    window.select_time(500)
    assert window.brain.sample == result.sample(500)
    window.invalidate_result()
    assert window.brain.result is None
    assert not window.brain.play.isEnabled()
    window.dirty = False
    window.close()


def test_fade_uses_cache_and_pause_preserves_position(app, result):
    from unittest.mock import patch

    window = MainWindow(auto_demo=False)
    presentation = window.presentation
    presentation.set_results([result, result])
    while len(presentation.cache) < 2:
        QTest.qWait(20)
    presentation.toggle()
    presentation.elapsed = 1.3
    with patch.object(
        presentation, "draw_frame", side_effect=AssertionError("No redraw in playback")
    ):
        presentation.tick()
        assert 0 < presentation.canvas.alpha < 1
        assert "Transisi visual" in presentation.title.text()
    alpha = presentation.canvas.alpha
    position = presentation.elapsed
    presentation.pause()
    assert presentation.canvas.second is not None
    assert presentation.canvas.alpha == alpha
    presentation.toggle()
    assert presentation.elapsed == position
    presentation.seek(1800)
    assert presentation.slider.value() == 1800
    assert presentation.elapsed == 1.8
    presentation.speed.setCurrentIndex(2)
    assert presentation.elapsed == 1.8
    with patch(
        "vard_eeg_erp.presentation.time.perf_counter", return_value=presentation.last_tick + 0.2
    ):
        presentation.tick()
    assert abs(presentation.elapsed - 1.9) < 1e-6
    presentation.seek(2990)
    with patch(
        "vard_eeg_erp.presentation.time.perf_counter", return_value=presentation.last_tick + 0.2
    ):
        presentation.tick()
    assert not presentation.timer.isActive()
    assert presentation.slider.value() == 3000
    presentation.toggle()
    assert presentation.elapsed == 0
    assert presentation.timer.isActive()
    presentation.reset()
    assert presentation.elapsed == 0
    assert presentation.slider.value() == 0
    assert not presentation.timer.isActive()
    window.close()


def test_signal_plots_bound_zoom_out(app, recording, result):
    window = MainWindow(auto_demo=False)
    window.install_recording(recording)
    window.install_result(result)
    for plot in (window.erp_plot, window.eeg_plot):
        view = plot.getViewBox()
        initial = view.viewRange()
        view.scaleBy((100, 100))
        for actual, expected in zip(view.viewRange(), initial):
            assert actual == pytest.approx(expected)
        view.scaleBy((0.5, 0.5))
        for actual, expected in zip(view.viewRange(), initial):
            assert actual[1] - actual[0] == pytest.approx((expected[1] - expected[0]) / 2)
        view.translateBy(x=1e9, y=1e9)
        for actual, expected in zip(view.viewRange(), initial):
            assert actual[0] >= expected[0] - 1e-8
            assert actual[1] <= expected[1] + 1e-8
    window.dirty = False
    window.close()


def test_vars_configuration_and_invalidation(app, result):
    from vard_eeg_erp.scoring_ui import ScoringPage

    page = ScoringPage()
    page.set_result(result)
    page.version.setText("test-only-1")
    page.reference.setText("synthetic fixture")
    for row in range(6):
        for column, value in enumerate(
            ["test ROI/window", "uV", "0", "10", str(1 / 6), "higher", "2"], 1
        ):
            page.grid.item(row, column).setText(value)
    page.calculate()
    assert page.output["composite"] == pytest.approx(20)
    assert page.output["analysis"] == result.history
    page.grid.item(0, 7).setText("3")
    assert page.output is None
    assert page.grid.item(0, 8).text() == ""
    page.calculate()
    assert page.output is not None
    page.set_result(None)
    assert page.output is None
    assert page.grid.item(0, 7).text() == ""
    page.close()
