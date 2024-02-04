# coding: utf-8

import time
import pymodbus  # To not delete this module reference!!
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

##!!!!##################################################################################################
#### Own written code can be placed above this commentblock . Do not change or delete commentblock! ####
########################################################################################################
##** Code created by generator - DO NOT CHANGE! **##

class Hs_modbusTCP_writer14185(hsl20_4.BaseModule):

    def __init__(self, homeserver_context):
        hsl20_4.BaseModule.__init__(self, homeserver_context, "hs_modbusTCP_writer14185")
        self.FRAMEWORK = self._get_framework()
        self.LOGGER = self._get_logger(hsl20_4.LOGGING_NONE,())
        self.PIN_I_MODBUS_SLAVE_IP=1
        self.PIN_I_PORT=2
        self.PIN_I_SLAVE_ID=3
        self.PIN_I_KEEP_ALIVE=4
        self.PIN_I_MODBUS_WORDORDER=5
        self.PIN_I_MODBUS_BYTEORDER=6
        self.PIN_I_ENABLE_DEBUG=7
        self.PIN_I_R1_ADDRESS=8
        self.PIN_I_R1_DATATYPE=9
        self.PIN_I_R1_NUM_VALUE=10
        self.PIN_I_R1_STR_VALUE=11
        self.PIN_I_R2_ADDRESS=12
        self.PIN_I_R2_DATATYPE=13
        self.PIN_I_R2_NUM_VALUE=14
        self.PIN_I_R2_STR_VALUE=15
        self.PIN_I_R3_ADDRESS=16
        self.PIN_I_R3_DATATYPE=17
        self.PIN_I_R3_NUM_VALUE=18
        self.PIN_I_R3_STR_VALUE=19
        self.PIN_I_R4_ADDRESS=20
        self.PIN_I_R4_DATATYPE=21
        self.PIN_I_R4_NUM_VALUE=22
        self.PIN_I_R4_STR_VALUE=23
        self.PIN_O_WRITE_COUNT=1
        self.PIN_O_ERROR_COUNT=2

########################################################################################################
#### Own written code can be placed after this commentblock . Do not change or delete commentblock! ####
###################################################################################################!!!##

        self.DEBUG = None
        self.client = None
        self.write_count = 0
        self.error_count = 0
        self.data_types = {
            'int8': {'method': 'add_8bit_int', 'minVal': -128, 'maxVal': 127},
            'uint8': {'method': 'add_8bit_uint', 'minVal': 0, 'maxVal': 255},
            'int16': {'method': 'add_16bit_int', 'minVal': -32768, 'maxVal': 32767},
            'uint16': {'method': 'add_16bit_uint', 'minVal': 0, 'maxVal': 65535},
            'int32': {'method': 'add_32bit_int', 'minVal': -2147483648, 'maxVal': 2147483647},
            'uint32': {'method': 'add_32bit_uint', 'minVal': 0, 'maxVal': 4294967295},
            'int64': {'method': 'add_64bit_int', 'minVal': -9223372036854775808,
                      'maxVal': 9223372036854775807},
            'uint64': {'method': 'add_64bit_uint', 'minVal': 0, 'maxVal': 18446744073709551615},
            'float32': {'method': 'add_32bit_float', 'minVal': -3.402823E+38,
                        'maxVal': 3.402823E+38},
            'float64': {'method': 'add_64bit_float', 'minVal': -1.79769313486232E+308,
                        'maxVal': 1.79769313486232E+308},
            'string': {'method': 'add_string'},
            'bool': {'coilWrite': True, 'minVal': 0, 'maxVal': 1}
        }

    def write_value(self, reg_address, reg_type, value):

        if reg_address < 0:  # Skip: Neg. values skips register execution
            return None

        ip_address = str(self._get_input_value(self.PIN_I_MODBUS_SLAVE_IP))
        port = int(self._get_input_value(self.PIN_I_PORT))
        unit_id = int(self._get_input_value(self.PIN_I_SLAVE_ID))

        try:
            self.log_debug("Conn IP:Port (UnitID)", ip_address + ":" + str(port) + " (" + str(unit_id) + ") ")
            if not self.client:
                self.client = ModbusTcpClient(ip_address, port, timeout=10, retry_on_empty=True, retry_on_invalid=True,
                                              reset_socket=False)
            if not self.client.is_socket_open():
                self.client.connect()

            register_settings = self.data_types.get(str(reg_type.split(';',1)[0]).lower())
            if not register_settings:  # No matching type entry found. lets skip over
                self.log_debug("No matching data type found: ", reg_type)
                return None

            # Bounce check
            if 'minVal' in register_settings and register_settings.get('minVal') > value:
                self.LOGGER.info("Skipping " + str(reg_address) + " of type " + reg_type + " because val "
                                 + str(value) + " fall below type limit!")
                return None
            if 'maxVal' in register_settings and register_settings.get('maxVal') < value:
                self.LOGGER.info("Skipping " + str(reg_address) + " of type " + reg_type + " because val "
                                 + str(value) + " exceeds type limit!")
                return None

            self.log_debug("Write type " + str(reg_type) + " in register  " + str(reg_address), str(value))

            # For simple datatype writes into a single register. Higher compatibility with
            # devices because not all support writing multiple registers.
            if 'method' in register_settings:
                builder = BinaryPayloadBuilder(byteorder=self.byte_order(), wordorder=self.word_order())
                getattr(builder, register_settings.get('method'))(value)
                payload = builder.build()

            handle = None
            reg_type_options = reg_type.split(';', 1)
            if len(reg_type_options) > 1 and str(reg_type_options[1]).lower() == "fc16":
                always_f16 = True
            else:
                always_f16 = False

            for attempt in range(3):
                if bool(register_settings.get('coilWrite', False)):  # Function code 5
                    handle = self.client.write_coil(reg_address, value, unit=unit_id)
                elif len(payload) == 1 and not always_f16:  # Function code 6
                    handle = self.client.write_register(reg_address, payload[0], skip_encode=True, unit=unit_id)
                else:  # Function code 16 (0x10)
                    handle = self.client.write_registers(reg_address, payload, skip_encode=True, unit=unit_id)

                self.log_debug("Response:", str(handle))

                if handle.isError():
                    time.sleep(0.1)
                else:
                    break

            # Increase write success count
            if not handle.isError():
                self.write_count += 1
                self._set_output_value(self.PIN_O_WRITE_COUNT, self.write_count)
            else:
                self.log_debug("Last exception msg logged", "Message: " + str(handle))

        except ConnectionException as con_err:
            self.log_debug("Last exception msg logged", "Message: " + str(con_err))
            self.LOGGER.error(str(con_err))
            self.error_count += 1
            self._set_output_value(self.PIN_O_ERROR_COUNT, self.error_count)
            if self.client:  # Lets start with a fresh client connection and object after the Exception
                self.client.close()
                self.client = None
        except Exception as err:
            self.log_debug("Last exception msg logged", "Message: " + str(err))
            self.LOGGER.error(str(err))
            self.error_count += 1
            self._set_output_value(self.PIN_O_ERROR_COUNT, self.error_count)
            if self.client:  # Lets start with a fresh client connection and object after the Exception
                self.client.close()
                self.client = None
            # Throw exception only if in debug mode
            if bool(self._get_input_value(self.PIN_I_ENABLE_DEBUG)):
                raise
        finally:
            if self.client and not bool(self._get_input_value(self.PIN_I_KEEP_ALIVE)):
                self.client.close()
                # Let's drop the client without keepalive to start with new client. Had an issue at 4.2.2023
                self.client = None

    def word_order(self):
        if bool(self._get_input_value(self.PIN_I_MODBUS_WORDORDER)):
            return Endian.Big
        else:
            return Endian.Little

    def byte_order(self):
        if bool(self._get_input_value(self.PIN_I_MODBUS_BYTEORDER)):
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
        elif index == self.PIN_I_MODBUS_SLAVE_IP or index == self.PIN_I_PORT or index == self.PIN_I_SLAVE_ID:
            self.client.close()
            self.client = None  # will recreate a connection after next use.

    def log_debug(self, key, value):
        if bool(self._get_input_value(self.PIN_I_ENABLE_DEBUG)):
            if not self.DEBUG:
                self.DEBUG = self.FRAMEWORK.create_debug_section()

            self.DEBUG.set_value(str(key), str(value))