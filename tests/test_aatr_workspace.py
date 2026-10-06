from unittest.mock import patch

from vard_eeg_erp.aatr_workspace import AATRWorkspace
from vard_eeg_erp.analysis import Settings
from vard_eeg_erp.app import create_application
from vard_eeg_erp.widgets import SettingsDialog


def test_filter_limits_and_invalid_baseline_keeps_dialog_open():
    app = create_application()
    dialog = SettingsDialog(Settings(), sfreq=80)
    assert dialog.fields['highpass'].maximum() == 10
    assert dialog.fields['lowpass'].maximum() < 40
    dialog.fields['baseline_start'].setValue(-500)
    with patch('vard_eeg_erp.widgets.QMessageBox.warning') as warning:
        dialog.validate_and_accept()
    warning.assert_called_once()
    assert dialog.result() == 0
    app.processEvents()


def test_active_erp_features_and_invalidation(result):
    app = create_application()
    page = AATRWorkspace(lambda: None)
    page.set_result(result)
    channel = page.channel.currentText()
    expected = result.metrics(channel, 0, 200)['mean_uv']
    assert page.grid.item(0, 1).text() == f'{expected:.4f}'
    page.set_result(None)
    assert page.grid.item(0, 1) is None
    page.close()
    app.processEvents()
