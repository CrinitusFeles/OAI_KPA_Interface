from PyQt5 import QtCore, Qt
from PyQt5.QtWidgets import QPushButton
import json


class DynamicButton(QPushButton):
    left_click = QtCore.pyqtSignal()

    def __init__(self, *__args, cmd=""):
        super().__init__(*__args)
        self.cmd = cmd

    def mousePressEvent(self, event):
        button = event.button()
        if button == Qt.Qt.LeftButton:
            self.left_click.emit()


class UpdateTableSignal(QtCore.QObject):
    update_table_signal = QtCore.pyqtSignal()


class Config:
    def __init__(self, **kwargs):
        self.uart_baudrate = kwargs.get('baudrate', 0)
        self.uart_channel = kwargs.get('channel', 0)
        self.uart_parity = kwargs.get('parity', 0)
        self.uart_stop_bit = kwargs.get('stop_bit', 0)
        self.serial_num = kwargs.get('serial_num', 0)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Commands:
    def __init__(self):
        self.cmd = []

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def create_json_file(config_obj, file_name):
    try:
        with open(file_name, 'w') as write_file:
            write_file.write(config_obj.to_json())
    except Exception as error:
        print(error)
