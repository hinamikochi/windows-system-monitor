from copy import deepcopy
import os

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QCheckBox,
                              QComboBox, QSlider, QLabel, QDialogButtonBox)
from PySide6.QtCore import Qt
from system_monitor.config.store import MODULES
from system_monitor.monitoring.disks import available_disks, default_disk


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('System Monitor Settings')
        self.setMinimumWidth(340)
        self.settings = deepcopy(settings)
        self.setStyleSheet('QDialog {background: #141a25;} QLabel, QCheckBox {color: #ecf1fa;} QComboBox, QPushButton {background: #293345; color: #ecf1fa; padding: 6px;}')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Visible modules'))
        self.modules = {}
        for key in MODULES:
            checkbox = QCheckBox(key.upper())
            checkbox.setChecked(settings['modules'][key])
            self.modules[key] = checkbox
            layout.addWidget(checkbox)
        form = QFormLayout()
        self.disk = QComboBox()
        selected = settings.get('disk_path', default_disk())
        try:
            disks = available_disks()
        except OSError:
            disks = []
        for root in disks:
            self.disk.addItem(root, root)
        if selected not in disks:
            self.disk.addItem(f'{selected} (unavailable)', selected)
        self.disk.setCurrentIndex(self.disk.findData(selected))
        form.addRow('Disk drive', self.disk)
        self.interval = QComboBox()
        for seconds in (1, 2, 5):
            self.interval.addItem(f'{seconds} second(s)', seconds)
        self.interval.setCurrentIndex(self.interval.findData(settings['interval']))
        form.addRow('Refresh', self.interval)
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(settings['background_opacity'])
        self.opacity_label = QLabel(f'{settings["background_opacity"]}%')
        self.opacity.valueChanged.connect(lambda value: self.opacity_label.setText(f'{value}%'))
        form.addRow('Background opacity', self.opacity)
        form.addRow('', self.opacity_label)
        layout.addLayout(form)
        self.pin = QCheckBox('Always on Top')
        self.pin.setChecked(settings['always_on_top'])
        layout.addWidget(self.pin)
        self.startup = QCheckBox('Start with Windows')
        self.startup.setChecked(settings['startup'])
        self.startup.setEnabled(os.name == 'nt')
        layout.addWidget(self.startup)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        result = deepcopy(self.settings)
        result.update(modules={key: checkbox.isChecked() for key, checkbox in self.modules.items()},
                      disk_path=self.disk.currentData(),
                      interval=self.interval.currentData(), background_opacity=self.opacity.value(),
                      always_on_top=self.pin.isChecked(), startup=self.startup.isChecked())
        return result
