# coding: utf-8

import time
import pymodbus  # To not delete this module reference!!
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient

##!!!!##################################################################################################
#### Own written code can be placed above this commentblock . Do not change or delete commentblock! ####
########################################################################################################
##** Code created by generator - DO NOT CHANGE! **##

class Hs_modbusTCP_writer14185(hsl20_3.BaseModule):

    def __init__(self, homeserver_context):
        hsl20_3.BaseModule.__init__(self, homeserver_context, "hs_modbusTCP_writer14185")
        self.FRAMEWORK = self._get_framework()
        self.LOGGER = self._get_logger(hsl20_3.LOGGING_NONE,())
        self.PIN_I_MODBUS_SLAVE_IP=1
        self.PIN_I_PORT=2
        self.PIN_I_SLAVE_ID=3
        self.PIN_I_MODBUS_WORDORDER=4
        self.PIN_I_MODBUS_BYTEORDER=5
        self.PIN_I_R1_ADDRESS=6
        self.PIN_I_R1_DATATYPE=7
        self.PIN_I_R1_NUM_VALUE=8
        self.PIN_I_R1_STR_VALUE=9
        self.PIN_I_R2_ADDRESS=10
        self.PIN_I_R2_DATATYPE=11
        self.PIN_I_R2_NUM_VALUE=12
        self.PIN_I_R2_STR_VALUE=13
        self.PIN_I_R3_ADDRESS=14
        self.PIN_I_R3_DATATYPE=15
        self.PIN_I_R3_NUM_VALUE=16
        self.PIN_I_R3_STR_VALUE=17
        self.PIN_I_R4_ADDRESS=18
        self.PIN_I_R4_DATATYPE=19
        self.PIN_I_R4_NUM_VALUE=20
        self.PIN_I_R4_STR_VALUE=21
        self.PIN_O_WRITE_COUNT=1
        self.FRAMEWORK._run_in_context_thread(self.on_init)

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.DEBUG = self.FRAMEWORK.create_debug_section()
        self.client = None
        self.counter = 0
        self.data_types = {
            'int8': {'method': 'add_8bit_int', 'singleWrite': False, 'minVal': -128, 'maxVal': 127},
            'uint8': {'method': 'add_8bit_uint', 'singleWrite': True, 'minVal': 0, 'maxVal': 255},
            'int16': {'method': 'add_16bit_int', 'singleWrite': False, 'minVal': -32768, 'maxVal': 32767},
            'uint16': {'method': 'add_16bit_uint', 'singleWrite': True, 'minVal': 0, 'maxVal': 65535},
            'int32': {'method': 'add_32bit_int', 'singleWrite': False, 'minVal': -2147483648, 'maxVal': 2147483647},
            'uint32': {'method': 'add_32bit_uint', 'singleWrite': False, 'minVal': 0, 'maxVal': 4294967295},
            'int64': {'method': 'add_64bit_int', 'singleWrite': False, 'minVal': -9223372036854775808,
                      'maxVal': 9223372036854775807},
            'uint64': {'method': 'add_64bit_uint', 'singleWrite': False, 'minVal': 0, 'maxVal': 18446744073709551615},
            'float32': {'method': 'add_32bit_float', 'singleWrite': False, 'minVal': -3.402823E+38,
                        'maxVal': 3.402823E+38},
            'float64': {'method': 'add_64bit_float', 'singleWrite': False, 'minVal': -1.79769313486232E+308,
                        'maxVal': 1.79769313486232E+308 },
            'string': {'method': 'add_string', 'singleWrite': False}
        }

    def write_value(self, reg_address, reg_type, value):

        if reg_address < 0:  # Skip: Neg. values skips register execution
            return None

        ip_address = str(self._get_input_value(self.PIN_I_MODBUS_SLAVE_IP))
        port = int(self._get_input_value(self.PIN_I_PORT))
        unit_id = int(self._get_input_value(self.PIN_I_SLAVE_ID))

        try:
            self.DEBUG.set_value("Conn IP:Port (UnitID)", ip_address + ":" + str(port) + " (" + str(unit_id) + ") ")
            if self.client is None:
                self.client = ModbusTcpClient(ip_address, port)
            if self.client.is_socket_open() is False:
                self.client.connect()

            register_settings = self.data_types.get(reg_type)
            if register_settings is None:  # No matching type entry found. lets skip over
                self.DEBUG.set_value("No matching data type found: ", reg_type)
                return None

            # Bounce check
            if reg_type != 'string' and register_settings.get('minVal') > value:
                self.LOGGER.info("Skipping " + str(reg_address) + " of type " + reg_type + " because val "
                                 + str(value) + " fall below type limit!")
                return None
            if reg_type != 'string' and register_settings.get('maxVal') < value:
                self.LOGGER.info("Skipping " + str(reg_address) + " of type " + reg_type + " because val "
                                 + str(value) + " exceeds type limit!")
                return None

            self.DEBUG.set_value("Write type " + str(reg_type) + " in register  " + str(reg_address), str(value))

            # For simple datatype writes without transforming into a single register. Higher compatibility with
            # devices because not all support writing multiple registers.
            handle = None
            for attempt in range(3):
                if register_settings.get('singleWrite'):
                    handle = self.client.write_register(reg_address, value, unit=unit_id)
                else:
                    builder = BinaryPayloadBuilder(byteorder=self.byte_order(), wordorder=self.word_order())
                    getattr(builder, register_settings.get('method'))(value)
                    payload = builder.build()
                    handle = self.client.write_registers(reg_address, payload, skip_encode=True, unit=unit_id)

                if handle.isError():
                    time.sleep(0.1)
                else:
                    break
                
            self.DEBUG.set_value("Response:", str(handle))

            # Increase write success count
            if not handle.isError():
                self.counter += 1
                self._set_output_value(self.PIN_O_WRITE_COUNT, self.counter)

        except Exception as err:
            self.DEBUG.set_value("Last exception msg logged", "Message: " + err.message)
            self.LOGGER.error(err)
            raise

    def word_order(self):
        if int(self._get_input_value(self.PIN_I_MODBUS_WORDORDER)) == 1:
            return Endian.Big
        else:
            return Endian.Little

    def byte_order(self):
        if int(self._get_input_value(self.PIN_I_MODBUS_BYTEORDER)) == 1:
            return Endian.Big
        else:
            return Endian.Little

    def on_init(self):
        return None

    def on_input_value(self, index, value):
        if index == self.PIN_I_R1_NUM_VALUE or index == self.PIN_I_R1_STR_VALUE:
            self.write_value(self._get_input_value(self.PIN_I_R1_ADDRESS),
                             self._get_input_value(self.PIN_I_R1_DATATYPE),
                             value)
        elif index == self.PIN_I_R2_NUM_VALUE or index == self.PIN_I_R2_STR_VALUE:
            self.write_value(self._get_input_value(self.PIN_I_R2_ADDRESS),
                             self._get_input_value(self.PIN_I_R2_DATATYPE),
                             value)
        elif index == self.PIN_I_R3_NUM_VALUE or index == self.PIN_I_R3_STR_VALUE:
            self.write_value(self._get_input_value(self.PIN_I_R3_ADDRESS),
                             self._get_input_value(self.PIN_I_R3_DATATYPE),
                             value)
        elif index == self.PIN_I_R4_NUM_VALUE or index == self.PIN_I_R4_STR_VALUE:
            self.write_value(self._get_input_value(self.PIN_I_R4_ADDRESS),
                             self._get_input_value(self.PIN_I_R4_DATATYPE),
                             value)
