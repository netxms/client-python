from enum import IntFlag
import ipaddress
import struct

class FieldType(IntFlag):
    INTEGER = 0
    STRING = 1
    INT64 = 2
    INT16 = 3
    BINARY = 4
    FLOAT = 5
    INETADDR = 6
    DETECT = 99

class MessageField():
    value = None

    def __init__(self, field_id, value, field_type=FieldType.DETECT):
        self.field_id = field_id
        self.value = value
        value_type = type(value)
        if field_type == FieldType.DETECT:
            if value_type is int:
                self.field_type = FieldType.INTEGER
            elif value_type is float:
                self.field_type = FieldType.FLOAT
            elif value_type is bytes:
                self.field_type = FieldType.BINARY
            elif value_type in (ipaddress.IPv4Address, ipaddress.IPv6Address, ipaddress.IPv4Network, ipaddress.IPv6Network):
                self.field_type = FieldType.INETADDR
            else:
                self.field_type = FieldType.STRING
        else:
            self.field_type = field_type

        if self.field_type == FieldType.INETADDR:
            if value_type is ipaddress.IPv4Address:
                self.value = ipaddress.IPv4Network(value)
            if value_type is ipaddress.IPv6Address:
                self.value = ipaddress.IPv6Network(value)

        if self.field_type not in FieldType:
            raise RuntimeError('Invalid field type')
    
    @classmethod
    def from_binary(cls, binary_field):
        (field_id, field_type) = struct.unpack('!IB', binary_field[:5])
        field_type = FieldType(field_type)
        offset = 6 # 5 + 1 byte padding
        if field_type == FieldType.INT16:
            value = struct.unpack_from('!H', binary_field, offset)[0]
            offset += 2
        else:
            offset += 2 # skip padding
            if field_type == FieldType.INTEGER:
                value = struct.unpack_from('!I', binary_field, offset)[0]
                offset += 4
            elif field_type == FieldType.INT64:
                value = struct.unpack_from('!Q', binary_field, offset)[0]
                offset += 8
            elif field_type == FieldType.FLOAT:
                value = struct.unpack_from('!d', binary_field, offset)[0]
                offset += 8
            elif field_type == FieldType.STRING:
                field_data_len = struct.unpack_from('!I', binary_field, offset)[0]
                offset += 4
                value = (binary_field[offset:offset + field_data_len]).decode('utf-16be')
                offset += field_data_len
            elif field_type == FieldType.FLOAT:
                raise RuntimeError('Not implemented')
            elif field_type == FieldType.INETADDR:
                address_data = binary_field[offset:offset + 16]
                offset += 16
                (family, mask) = struct.unpack_from('!BB', binary_field, offset)
                if family == 0:
                    value = ipaddress.IPv4Network(address_data[:4], mask)
                elif family == 1:
                    value = ipaddress.IPv6Network(address_data, mask)
                    pass
                else:
                    # UNSPEC
                    value = None
                offset += 8 # 2 bytes data + padding
            elif field_type == FieldType.BINARY:
                field_data_len = struct.unpack_from('!I', binary_field, offset)[0]
                offset += 4
                value = binary_field[offset:offset + field_data_len]
                offset += field_data_len
            else:
                raise RuntimeError('Unknown field type (%d)' % (field_type))
        f = cls(field_id, value, field_type)
        padding = offset % 8
        if padding != 0:
            offset += 8 - padding
        return (f, offset)

    def serialize(self):
        output = struct.pack('!IBB',
            self.field_id,
            self.field_type,
            0
        )
        if self.field_type == FieldType.INT16:
            output += struct.pack('!H',
            self.value
        )
        else:
            output += struct.pack('!H', 0)
            if self.field_type == FieldType.INTEGER:
                output += struct.pack('!I', self.value)
            elif self.field_type == FieldType.INT64:
                output += struct.pack('!Q', self.value)
            elif self.field_type == FieldType.FLOAT:
                output += struct.pack('!d', self.value)
            elif self.field_type == FieldType.STRING:
                output += struct.pack('!I', len(self.value) * 2)
                output += self.value.encode('utf-16be')
            elif self.field_type == FieldType.BINARY:
                output += struct.pack('!I', len(self.value))
                output += self.value
            elif self.field_type == FieldType.INETADDR:
                value_type = type(self.value)
                if value_type is ipaddress.IPv4Network:
                    output += self.value.network_address.packed
                    output += b'\000' * 12
                    output += b'\000'
                elif value_type is ipaddress.IPv6Network:
                    output += self.value.network_address.packed
                    output += b'\001'
                else:
                    output += b'\000' * 16
                    output += b'\002'
                output += struct.pack('!B', self.value.prefixlen)
                output += b'\000' * 6
            else:
                raise RuntimeError("Unknown field type (%d)" % self.field_type)
        padding = len(output) % 8
        if padding != 0:
            output += b'\0' * (8 - padding)
        return output

    def __repr__(self):
        return 'MessageField{id=%d,type=%s,value=%s}' % (
            self.field_id,
            self.field_type,
            self.value
            )

""" Message Flags """
class Flags(IntFlag):
    BINARY = 0x0001
    END_OF_FILE = 0x0002
    DONT_ENCRYPT = 0x0004
    END_OF_SEQUENCE = 0x0008
    REVERSE_ORDER = 0x0010
    CONTROL = 0x0020
    COMPRESSED = 0x0040
    STREAM = 0x0080

class Message():
    HEADER_SIZE = 16

    def __init__(self, message_code, message_id = 0, **kwargs):
        self.message_code = message_code
        self.message_id = message_id
        self.flags = 0
        self.binary = False
        self.control = False
        self.fields = {}

        if 'binary_message' in kwargs:
            self.deserialize(kwargs.get('binary_message'))

    @classmethod
    def from_binary(cls, binary_message):
        return Message(None, None, binary_message=binary_message)

    @property
    def control(self):
        return self.flags & Flags.CONTROL == Flags.CONTROL

    @control.setter
    def control(self, new_value):
        if new_value:
            self.flags |= Flags.CONTROL
        else:
            self.flags &= ~int(Flags.CONTROL)

    @property
    def binary(self):
        return self.flags & Flags.BINARY == Flags.BINARY

    @binary.setter
    def binary(self, new_value):
        if new_value:
            self.flags |= Flags.BINARY
        else:
            self.flags &= ~int(Flags.BINARY)

    @property
    def control_data(self):
        return self._control_data

    @control_data.setter
    def control_data(self, new_value):
        self._control_data = new_value
        self.control = True
    
    @property
    def binary_data(self):
        return self._binary_data
    
    @binary_data.setter
    def binary_data(self, new_value):
        self._binary_data = new_value
        self.binary = True

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, new_value):
        if hasattr(self, '_Message_fields'):
            raise AttributeError("Attribute is read-only")
        self._fields = new_value

    def set(self, code, value, field_type=FieldType.DETECT):
        self._fields[code] = MessageField(code, value, field_type)
    
    def set_int16(self, code, value):
        self.set(code, value, FieldType.INT16)
    
    def set_int64(self, code, value):
        self.set(code, value, FieldType.INT64)

    def get(self, code):
        if code in self._fields:
            return self._fields[code]

    def serialize(self):
        if self.control:
            return struct.pack("!HHIII",
                self.message_code,
                self.flags,
                self.HEADER_SIZE,
                self.message_id,
                self._control_data
            )
        elif self.binary:
            padding = (8 - (len(self._binary_data) % 8)) & 7
            packetSize = len(self._binary_data) + self.HEADER_SIZE + padding
            output = struct.pack("!HHIII",
                self.message_code,
                self.flags,
                packetSize,
                self.message_id,
                len(self._binary_data)
            )
            output += self._binary_data
            output += struct.pack('B', 0) * padding
            return output
        else:
            payload = b''
            for key in sorted(self._fields): # order is important only for test
                field = self._fields[key]
                payload += field.serialize()

            header = struct.pack("!HHIII",
                self.message_code,
                self.flags,
                len(payload) + self.HEADER_SIZE,
                self.message_id,
                len(self.fields)
            )

            return header + payload
        return None
    
    def deserialize(self, binary_message):
        if len(binary_message) < self.HEADER_SIZE:
            raise RuntimeError('Binary message is smaller than header size')

        header = struct.unpack("!HHIII", binary_message[:self.HEADER_SIZE])
        (self.message_code, self.flags, message_size, self.message_id, data) = header

        if len(binary_message) != message_size:
            raise RuntimeError('Binary message size does not match value in header')

        if self.control:
            self._control_data = data
        elif self.binary:
            binary_len = data
            if binary_len > len(binary_message) - self.HEADER_SIZE:
                raise RuntimeError('Invalid binary data len')
            self._binary_data = binary_message[self.HEADER_SIZE:self.HEADER_SIZE+binary_len]
        else:
            number_of_fields = data
            offset = self.HEADER_SIZE
            for _ in range(0, number_of_fields):
                (field, bytes_consumed) = MessageField.from_binary(binary_message[offset:])
                offset += bytes_consumed
                if offset > len(binary_message):
                    raise RuntimeError('Message truncated')
                self._fields[field.field_id] = field

    def __repr__(self):
        return "Message{code=%d, id=%d, flags=%d, binary=%s, control=%s, fields=%s}" % (
            self.message_code,
            self.message_id,
            self.flags,
            'YES' if self.binary else 'NO',
            'YES' if self.control else 'NO',
            self.fields
        )