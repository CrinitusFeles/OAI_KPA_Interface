from OaiModbus import OaiModbus
import time


class OaiDigitalModule:
    def __init__(self):

        self.client = OaiModbus()
        self.client.connect()
        self.client.continuously_ao_flag = True
        self.client.continuously_ai_flag = True
        self.client.ai_read_ranges = [[0, 14]]
        self.client.start_continuously_queue_reading()

        self.packet_counter = 0

        # -------------- Register adresses --------------------- #
        self.uart1_recieve_struct_addr = 14
        self.uart1_write_ptr_addr = self.uart1_recieve_struct_addr + 2
        self.uart1_receive_data_addr = self.uart1_recieve_struct_addr + 4

        self.uart1_transmit_struct_addr = 1072
        self.uart1_scaler_addr = self.uart1_transmit_struct_addr
        self.uart1_start_flag_addr = self.uart1_transmit_struct_addr + 1
        self.uart1_transmit_flag_addr = self.uart1_transmit_struct_addr + 2
        self.uart1_data_len_addr = self.uart1_transmit_struct_addr + 3
        self.uart1_transmit_data_addr = self.uart1_transmit_struct_addr + 4
        
        self.uart1_setting_struct_addr = 1140
        self.uart1_setting_scaler_addr = self.uart1_setting_struct_addr
        self.uart1_setting_low_baud = self.uart1_setting_struct_addr + 1
        self.uart1_setting_high_baud = self.uart1_setting_struct_addr + 2
        self.uart1_setting_low_word_length = self.uart1_setting_struct_addr + 3
        self.uart1_setting_high_word_length = self.uart1_setting_struct_addr + 4
        self.uart1_setting_low_stop_bits = self.uart1_setting_struct_addr + 5
        self.uart1_setting_high_stop_bits = self.uart1_setting_struct_addr + 6
        self.uart1_setting_low_parity = self.uart1_setting_struct_addr + 7
        self.uart1_setting_high_parity = self.uart1_setting_struct_addr + 8
        self.uart1_setting_flag = self.uart1_setting_struct_addr + 9

        self.uart2_recieve_struct_addr = 1042
        self.uart2_write_ptr_addr = self.uart2_recieve_struct_addr + 2
        self.uart2_receive_data_addr = self.uart2_recieve_struct_addr + 4

        self.uart2_transmit_struct_addr = 1150
        self.uart2_start_flag_addr = self.uart2_transmit_struct_addr + 1
        self.uart2_transmit_flag_addr = self.uart2_transmit_struct_addr + 2
        self.uart2_data_len_addr = self.uart2_transmit_struct_addr + 3
        self.uart2_transmit_data_addr = self.uart2_transmit_struct_addr + 4
        
        self.uart2_setting_struct_addr = 1218
        self.uart2_setting_scaler_addr = self.uart2_setting_struct_addr
        self.uart2_setting_low_baud = self.uart2_setting_struct_addr + 1
        self.uart2_setting_high_baud = self.uart2_setting_struct_addr + 2
        self.uart2_setting_low_word_length = self.uart2_setting_struct_addr + 3
        self.uart2_setting_high_word_length = self.uart2_setting_struct_addr + 4
        self.uart2_setting_low_stop_bits = self.uart2_setting_struct_addr + 5
        self.uart2_setting_high_stop_bits = self.uart2_setting_struct_addr + 6
        self.uart2_setting_low_parity = self.uart2_setting_struct_addr + 7
        self.uart2_setting_high_parity = self.uart2_setting_struct_addr + 8
        self.uart2_setting_flag = self.uart2_setting_struct_addr + 9
        # ======================================================= #

    def get_analog_inputs(self):
        return self.client.ai_register_map[:8]

    def uart_send(self, data):
        # at first we write data to data registers and their amount
        self.packet_counter += 1
        self.client.write_ranges = [[self.uart1_scaler_addr, [self.packet_counter]],
                                    [self.uart1_data_len_addr, [len(data)]], [self.uart1_transmit_data_addr, data]]
        # print('write ranges: ', self.client.write_ranges)
        self.client.write_regs()
        # at the end we just set start flag
        self.client.write_ranges = [[self.uart1_start_flag_addr, [1]]]
        self.client.write_regs()

    def uart_read(self, length):
        self.client.ai_read_ranges = [[self.uart1_receive_data_addr, self.uart1_receive_data_addr + length]]
        self.client.read_regs(target='ai')
        return self.client.ai_register_map[self.uart1_receive_data_addr:self.uart1_receive_data_addr + length]

    def uart_get_tx_struct(self):
        self.client.ao_read_ranges = [[self.uart1_transmit_struct_addr, self.uart1_transmit_data_addr + 10]]
        self.client.read_regs(target='ao')
        return {'scaler': self.client.ao_register_map[self.uart1_scaler_addr],
                'start': self.client.ao_register_map[self.uart1_start_flag_addr],
                'transmit flag': self.client.ao_register_map[self.uart1_transmit_flag_addr],
                'len': self.client.ao_register_map[self.uart1_data_len_addr],
                'data': self.client.ao_register_map[self.uart1_transmit_data_addr:
                                                    self.uart1_transmit_data_addr +
                                                    self.client.ao_register_map[self.uart1_data_len_addr]]}
        # return self.client.ao_register_map[self.uart1_transmit_struct_addr:self.uart1_transmit_data_addr + 5]

    def uart_get_rx_struct(self):
        self.client.ai_read_ranges = [[self.uart1_recieve_struct_addr, self.uart1_receive_data_addr + 10]]
        self.client.read_regs(target='ai')
        return {'write_ptr': self.client.ai_register_map[self.uart1_write_ptr_addr],
                'data': self.client.ai_register_map[self.uart1_receive_data_addr:
                                                    self.uart1_receive_data_addr +
                                                    self.client.ai_register_map[self.uart1_write_ptr_addr]]}
        # return self.client.ao_register_map[self.uart1_recieve_struct_addr:self.uart1_receive_data_addr + 5]


if __name__ == '__main__':
    dig_mod = OaiDigitalModule()
    while True:
        print('ADC channels: ', dig_mod.get_analog_inputs())
        time.sleep(1)
        dig_mod.uart_send([0, 1, 0, 2, 0, 3, 0, 4, 0, 5])
        time.sleep(1)
        print('uart tx struct: ', dig_mod.uart_get_tx_struct())
        time.sleep(1)
        print('uart rx struct: ', dig_mod.uart_get_rx_struct())
        time.sleep(1)
