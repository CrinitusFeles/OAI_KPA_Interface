from oai_modbus import OAI_Modbus
import time
import struct
import json


class UartStruct:
    def __init__(self, **kwargs):
        self.receive_struct_addr = kwargs.get('receive_struct_addr', 14)
        self.write_ptr_addr = self.receive_struct_addr + 3
        self.receive_data_addr = self.receive_struct_addr + 4

        self.transmit_struct_addr = kwargs.get('transmit_struct_addr', 1072)
        self.scaler_addr = self.transmit_struct_addr
        self.start_flag_addr = self.transmit_struct_addr + 1
        self.transmit_flag_addr = self.transmit_struct_addr + 2
        self.data_len_addr = self.transmit_struct_addr + 3
        self.transmit_data_addr = self.transmit_struct_addr + 4

        self.setting_struct_addr = kwargs.get('setting_struct_addr', 1140)
        self.setting_scaler_addr = self.setting_struct_addr
        self.setting_low_baud = self.setting_struct_addr + 1
        self.setting_high_baud = self.setting_struct_addr + 2
        self.setting_low_word_length = self.setting_struct_addr + 3
        self.setting_high_word_length = self.setting_struct_addr + 4
        self.setting_low_stop_bits = self.setting_struct_addr + 5
        self.setting_high_stop_bits = self.setting_struct_addr + 6
        self.setting_low_parity = self.setting_struct_addr + 7
        self.setting_high_parity = self.setting_struct_addr + 8
        self.setting_flag = self.setting_struct_addr + 9
        
        self.rx_packet_counter = 0
        self.tx_packet_counter = 0

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class OaiDigitalModule:
    def __init__(self, **kwargs):

        self.client = OAI_Modbus(**kwargs)
        # self.client.connect()
        self.client.continuously_ao_flag = True
        self.client.continuously_ai_flag = True
        self.client.ai_read_ranges = [[0, 14]]
        # self.client.start_continuously_queue_reading()

        # -------------- Register adresses --------------------- #
        self.uart1 = UartStruct(receive_struct_addr=14, transmit_struct_addr=1072, setting_struct_addr=1140)
        self.uart2 = UartStruct(receive_struct_addr=1042, transmit_struct_addr=1150, setting_struct_addr=1218)

        self.ina226_3v_struct_addr = 8
        self.ina226_5v_struct_addr = 11
        # ======================================================= #

    def connect(self):
        return self.client.connect()

    def disconnect(self):
        self.client.disconnect()

    def get_analog_inputs(self):
        self.client.read_regs(target='ai', read_ranges=[[0, 8]])
        return self.client.ai_register_map[:8]

    def uart_send(self, data_bytes=None, uart=None):
        # at first we write data to data registers and their amount
        # uart.tx_packet_counter += 1
        data_16bit = []

        if len(data_bytes) % 2 == 1:
            data_bytes.insert(-1, 0)
        for i in range(0, len(data_bytes), 2):
            data_16bit.append(struct.unpack('>H', struct.pack('BB', *data_bytes[i:i+2]))[0])
        # print("data_16bit: ", data_16bit)
        self.client.write_ranges = [[uart.start_flag_addr, [1]],
                                    [uart.data_len_addr, [len(data_bytes)]],
                                    [uart.transmit_data_addr, data_16bit]]

        # print('write ranges: ', self.client.write_ranges)
        self.client.write_regs_ranges()

        # at the end we just set start flag
        self.client.write_regs(offset=uart.scaler_addr, data_list=[1])

    def uart_read(self, length, uart=None):
        self.client.read_regs(target='ai', read_ranges=[[uart.receive_data_addr, uart.receive_data_addr + length]])
        return self.client.ai_register_map[uart.receive_data_addr:uart.receive_data_addr + length]

    def uart_get_tx_struct(self, uart=None):
        self.client.read_regs(target='ao', read_ranges=[[uart.transmit_struct_addr, uart.transmit_data_addr + 10]])
        return {'scaler': self.client.ao_register_map[uart.scaler_addr],
                'start': self.client.ao_register_map[uart.start_flag_addr],
                'transmit flag': self.client.ao_register_map[uart.transmit_flag_addr],
                'len': self.client.ao_register_map[uart.data_len_addr],
                'data': self.client.ao_register_map[uart.transmit_data_addr:
                                                    uart.transmit_data_addr +
                                                    self.client.ao_register_map[uart.data_len_addr] // 2]}

    def uart_get_rx_struct(self, uart=None):

        self.client.read_regs(target='ai', read_ranges=[[uart.receive_struct_addr, uart.receive_data_addr +
                                                         self.client.ai_register_map[uart.write_ptr_addr] +
                                                         self.client.ao_register_map[uart.data_len_addr] // 2]])
        print("read len: ", uart.receive_data_addr - uart.receive_data_addr +
              self.client.ai_register_map[uart.write_ptr_addr] +
              self.client.ao_register_map[uart.data_len_addr] // 2)
        # print("rx: ", self.client.ai_register_map[uart.receive_data_addr:uart.receive_data_addr+16])
        return {'write_ptr': self.client.ai_register_map[uart.write_ptr_addr],
                'data': self.client.ai_register_map[uart.receive_data_addr:
                                                    uart.receive_data_addr +
                                                    self.client.ai_register_map[uart.write_ptr_addr]//2]}


if __name__ == '__main__':
    dig_mod = OaiDigitalModule(serial_num=['20703699424D'])
    if dig_mod.connect():
        print("success connection")
        while True:
            print('ADC channels: ', dig_mod.get_analog_inputs())
            time.sleep(1)
            dig_mod.uart_send([1, 2, 3, 4, 5, 6], dig_mod.uart1)
            time.sleep(1)
            print('uart tx struct: ', dig_mod.uart_get_tx_struct(dig_mod.uart1))
            time.sleep(1)
            print('uart rx struct: ', dig_mod.uart_get_rx_struct(dig_mod.uart1))
            time.sleep(1)
