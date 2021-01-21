from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QTableWidgetItem
import threading
import time
import json
import os.path
from . import oai_kpa_interface_gui
from . import utils
from . import oai_kpa_interface


class OAI_KPA_Interface_controller(QWidget, oai_kpa_interface_gui.Ui_Form):

    def __init__(self):
        # ------------------- window init ------------------------ #
        super().__init__()
        self.setupUi(self)
        self.setMinimumHeight(485)
        self.setWindowTitle('OAI KPA Interface')
        # ======================================================== #

        # ------------------ custom signals -------------------- #
        self.update_table_signal_obj = utils.UpdateTableSignal()
        self.update_table_signal_obj.update_table_signal.connect(self.update_table)
        # ======================================================== #

        # ------------------ connect signals -------------------- #
        self.uart_connect_button.pressed.connect(self.connect_device)
        self.uart_serial_num_refresh_button.pressed.connect(self.refresh_serial_num_list)
        self.uart_serial_num_combobox.currentIndexChanged.connect(self.update_serial_num_in_line_edit)
        self.send_in_uart_button.pressed.connect(self.uart_transmit)
        self.reload_file_button.pressed.connect(self.reload_log_file)
        self.clear_browser_button.pressed.connect(self.clear_log_browser)
        self.print_in_browser_checkbox.pressed.connect(self.log_browser_change_condition)
        self.print_in_file_checkbox.pressed.connect(self.log_file_change_condition)
        # ====================================================== #
        self.interface = oai_kpa_interface.OaiDigitalModule(serial_num=['20703699424D'], debug=True)
        self.single_window = True
        self.read_continuously_flag = False
        self.config_file_name = "config.json"
        self.command_file_name = "commands.json"
        self.ai_read_thread = None

        # ------------------ uart variables -------------------- #
        self.ai_list = []
        self.uart_last_parcel = []
        self.rx_struct = {}
        self.last_write_ptr = 0
        if self.uart_ch_combobox.currentText() == 'UART 1':
            self.uart = self.interface.uart1
        else:
            self.uart = self.interface.uart2
        # ====================================================== #

        if not self.search_command_file():
            print("command file does not exist")
            command_obj = utils.Commands()
            command_obj.cmd = [['start', '0, 1, 2, 3'], ['stop', '2, 3, 4, 5']]
            utils.create_json_file(command_obj, self.command_file_name)
        else:
            with open(self.command_file_name, "r") as read_file:
                command_obj = utils.Commands()
                command_obj.__dict__ = json.load(read_file)
                print(command_obj.cmd)
                if len(command_obj.cmd) == 0:
                    self.scroll_area.close()
                else:
                    for i in command_obj.cmd:
                        btn = utils.DynamicButton(i[0], self, cmd=i[1])
                        btn.left_click.connect(self.dynamic_button_pressed)
                        self.vbox.addWidget(btn)

                    self.scroll_area.setLayout(self.vbox)

        if not self.search_config_file():
            print("config file does not exist")
            config_obj = utils.Config(channel=0, baudrate=1, parity=0, stop_bit=0, serial_num=5)
            utils.create_json_file(config_obj, self.config_file_name)
        else:
            print("config file exists")
            try:
                with open(self.config_file_name, "r") as read_file:
                    config_obj = utils.Config()
                    config_obj.__dict__ = json.load(read_file)

                    self.uart_ch_combobox.setCurrentIndex(config_obj.uart_channel)
                    self.uart_baudrate_combobox.setCurrentIndex(config_obj.uart_baudrate)
                    self.uart_parity_combobox.setCurrentIndex(config_obj.uart_parity)
                    self.uart_stop_bit_combobox.setCurrentIndex(config_obj.uart_stop_bit)
                    self.uart_serial_num_line_edit.setText(config_obj.serial_num)
            except Exception as error:
                print(error)

        if not self.single_window:
            self.widget_3.close()

    def search_config_file(self):
        return os.path.isfile(self.config_file_name) and os.stat(self.config_file_name).st_size != 0

    def search_command_file(self):
        return os.path.isfile(self.command_file_name) and os.stat(self.command_file_name).st_size != 0

    def connect_device(self):
        try:
            if self.uart_connect_button.text() == "Connect":
                config_obj = utils.Config(channel=0, baudrate=1, parity=0, stop_bit=0, serial_num=5)
                config_obj.uart_channel = self.uart_ch_combobox.currentIndex()
                config_obj.uart_baudrate = self.uart_baudrate_combobox.currentIndex()
                config_obj.uart_parity = self.uart_parity_combobox.currentIndex()
                config_obj.uart_stop_bit = self.uart_stop_bit_combobox.currentIndex()
                config_obj.serial_num = self.uart_serial_num_line_edit.text()

                with open(self.config_file_name, 'w') as file:
                    file.write(config_obj.to_json())

                if self.interface.connect() == 1:
                    self.uart_connect_button.setText("Disconnect")
                    self.read_continuously_flag = True
                    self.ai_read_thread = threading.Thread(name='ai_read', target=self.__read_routine, daemon=True)
                    self.ai_read_thread.start()

                    if not self.ai_read_thread.is_alive():
                        self.read_continuously_flag = False
                        print("some error with thread")
                else:
                    self.uart_connect_button.setText("Error connection")

            else:
                self.uart_connect_button.setText("Connect")
                self.read_continuously_flag = False
                self.interface.disconnect()
                self.update_table()
        except Exception as error:
            print("error in func connect_device")
            print(error)

    def refresh_serial_num_list(self):
        self.uart_serial_num_combobox.clear()
        devices = self.interface.client.get_connected_devices()

        for i in devices:
            if i[1] != '':
                self.uart_serial_num_combobox.addItem(i[1])

    def update_serial_num_in_line_edit(self):
        self.uart_serial_num_line_edit.setText(self.uart_serial_num_combobox.currentText())

    def uart_transmit(self):
        if self.send_in_uart_line_edit.text() != "":
            input_array = self.send_in_uart_line_edit.text().replace(',', ' ').replace(';', ' ').split(' ')
            uart_send_byte_array = [int(byte) for byte in input_array]
            print("uart tx: ", uart_send_byte_array)
            self.interface.uart_send(data_bytes=uart_send_byte_array, uart=self.uart)
            self.log_browser.append("tx[" + str(self.uart.tx_packet_counter) + "] -> " + self.send_in_uart_line_edit.text())
            self.uart.tx_packet_counter += 1

    def reload_log_file(self):
        pass

    def clear_log_browser(self):
        self.log_browser.clear()

    def log_browser_change_condition(self):
        pass

    def log_file_change_condition(self):
        pass

    def update_table(self):
        try:
            # self.ai_list = [0, 1, 2, 3, 4, 5, 6, 7]
            # print(self.ai_list)
            counter = 0
            for i in self.ai_list:
                if self.interface.client.connection_status:
                    self.analog_inputs_table.setItem(0, counter, QTableWidgetItem(str(i)))
                    if i > 3100:
                        self.analog_inputs_table.item(counter, 0).setBackground(QtGui.QColor(255, 0, 0))
                    elif 1100 < i <= 3100:
                        self.analog_inputs_table.item(counter, 0).setBackground(QtGui.QColor(255, 196, 0))
                    else:
                        self.analog_inputs_table.item(counter, 0).setBackground(QtGui.QColor(0, 255, 0))
                    counter += 1
                else:
                    self.analog_inputs_table.item(counter, 0).setBackground(QtGui.QColor(255, 255, 255))
                    counter += 1

        except Exception as error:
            print(error)

    def __read_routine(self):
        self.rx_struct = self.interface.uart_get_rx_struct(self.uart)
        self.last_write_ptr = self.rx_struct.get('write_ptr')
        while self.read_continuously_flag:
            try:
                self.ai_list = self.interface.get_analog_inputs()
                self.rx_struct = self.interface.uart_get_rx_struct(self.uart)
                if self.last_write_ptr != self.rx_struct.get('write_ptr'):
                    print("last write_ptr before = ", self.last_write_ptr)
                    self.log_browser.append('rx[' + str(self.uart.rx_packet_counter) + '] <- ' +
                                            str(self.rx_struct.get('data')))
                    self.last_write_ptr = self.rx_struct.get('write_ptr')
                    print("last write_ptr after = ", self.last_write_ptr)
                    self.uart.rx_packet_counter += 1
                self.update_table_signal_obj.update_table_signal.emit()
                time.sleep(0.2)
            except Exception as error:
                print(error)

    def dynamic_button_pressed(self):
        print(self.sender().cmd)
        self.log_browser.append("tx[" + str(self.uart.tx_packet_counter) + "] -> " + self.sender().cmd)
        self.uart.tx_packet_counter += 1

