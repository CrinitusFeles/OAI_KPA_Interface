from oai_modbus import OAI_Modbus
import time
import struct


class UartStruct:
    def __init__(self, **kwargs):
        self.receive_struct_addr = kwargs.get('receive_struct_addr', 14)
        self.write_ptr_addr = self.receive_struct_addr + 2
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


class OaiDigitalModule:
    def __init__(self, **kwargs):

        self.client = OAI_Modbus(**kwargs)
        self.client.connect()
        self.client.continuously_ao_flag = True
        self.client.continuously_ai_flag = True
        self.client.ai_read_ranges = [[0, 14]]
        self.client.start_continuously_queue_reading()

        self.packet_counter = 0

        # -------------- Register adresses --------------------- #
        self.uart1 = UartStruct(receive_struct_addr=14, transmit_struct_addr=1072, setting_struct_addr=1140)
        self.uart2 = UartStruct(receive_struct_addr=1042, transmit_struct_addr=1150, setting_struct_addr=1218)
        # ======================================================= #

    def get_analog_inputs(self):
        return self.client.ai_register_map[:8]

    def uart_send(self, data_bytes):
        # at first we write data to data registers and their amount
        self.packet_counter += 1
        data_16bit = []

        if len(data_bytes) % 2 == 1:
            data_bytes.insert(-1, 0)
        for i in range(0, len(data_bytes), 2):
            data_16bit.append(struct.unpack('>H', struct.pack('BB', *data_bytes[i:i+2]))[0])
        # print("data_16bit: ", data_16bit)
        self.client.write_ranges = [[self.uart1.start_flag_addr, [1]],
                                    [self.uart1.data_len_addr, [len(data_bytes)]],
                                    [self.uart1.transmit_data_addr, data_16bit]]

        # print('write ranges: ', self.client.write_ranges)
        self.client.write_regs()

        # at the end we just set start flag
        self.client.write_ranges = [[self.uart1.scaler_addr, [self.packet_counter]]]
        self.client.write_regs()

    def uart_read(self, length):
        self.client.ai_read_ranges = [[self.uart1.receive_data_addr, self.uart1.receive_data_addr + length]]
        self.client.read_regs(target='ai')
        return self.client.ai_register_map[self.uart1.receive_data_addr:self.uart1.receive_data_addr + length]

    def uart_get_tx_struct(self):
        self.client.ao_read_ranges = [[self.uart1.transmit_struct_addr, self.uart1.transmit_data_addr + 10]]
        self.client.read_regs(target='ao')
        return {'scaler': self.client.ao_register_map[self.uart1.scaler_addr],
                'start': self.client.ao_register_map[self.uart1.start_flag_addr],
                'transmit flag': self.client.ao_register_map[self.uart1.transmit_flag_addr],
                'len': self.client.ao_register_map[self.uart1.data_len_addr],
                'data': self.client.ao_register_map[self.uart1.transmit_data_addr:
                                                    self.uart1.transmit_data_addr +
                                                    self.client.ao_register_map[self.uart1.data_len_addr] // 2]}
        # return self.client.ao_register_map[self.uart1.transmit_struct_addr:self.uart1.transmit_data_addr + 5]

    def uart_get_rx_struct(self):
        self.client.ai_read_ranges = [[self.uart1.receive_struct_addr, self.uart1.receive_data_addr + 25]]
        self.client.read_regs(target='ai')
        # print("rx: ", self.client.ai_register_map[self.uart1.receive_data_addr:self.uart1.receive_data_addr+16])
        return {'write_ptr': self.client.ai_register_map[self.uart1.write_ptr_addr],
                'data': self.client.ai_register_map[self.uart1.receive_data_addr:
                                                    self.uart1.receive_data_addr +
                                                    self.client.ai_register_map[self.uart1.write_ptr_addr]//2]}
        # return self.client.ao_register_map[self.uart1.receive_struct_addr:self.uart1.receive_data_addr + 5]


if __name__ == '__main__':
    dig_mod = OaiDigitalModule()
    while True:
        print('ADC channels: ', dig_mod.get_analog_inputs())
        time.sleep(1)
        dig_mod.uart_send([1, 2, 3, 4, 5, 6])
        time.sleep(1)
        print('uart tx struct: ', dig_mod.uart_get_tx_struct())
        time.sleep(1)
        print('uart rx struct: ', dig_mod.uart_get_rx_struct())
        time.sleep(1)
