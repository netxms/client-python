import unittest
import netxms
import ipaddress

class TestNXCPMessage(unittest.TestCase):
    def test_flags(self):
        m = netxms.Message(100)
        self.assertEqual(m.flags, 0)
        m.control = True
        self.assertEqual(m.flags, netxms.message.Flags.CONTROL)
        m.control = False
        self.assertEqual(m.flags, 0)
        m.binary = True
        self.assertEqual(m.flags, netxms.message.Flags.BINARY)
        m.binary = False
        self.assertEqual(m.flags, 0)
        m.control = True
        m.binary = True
        self.assertEqual(m.flags, netxms.message.Flags.CONTROL | netxms.message.Flags.BINARY)
        m.flags = 0xFFFF0000
        self.assertEqual(m.flags, 0xFFFF0000)
        m.control = True
        m.binary = True
        self.assertEqual(m.flags, 0xFFFF0021)

    def test_fieldtypes(self):
        m = netxms.Message(100)
        m.set(100, "Test")
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.STRING)
        m.set(100, 1)
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.INTEGER)
        m.set(100, 1.0)
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.FLOAT)
        m.set_int16(100, 1)
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.INT16)
        m.set_int64(100, 1)
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.INT64)
        m.set(100, ipaddress.ip_address('1.2.3.4'))
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.INETADDR)
        m.set(100, b'')
        self.assertEqual(m._fields[100].field_type, netxms.message.FieldType.BINARY)

    def test_serialize_control(self):
        m = netxms.Message(100)
        m.control_data = 200
        self.assertEqual(m.flags, netxms.message.Flags.CONTROL)
        serialized = m.serialize()
        self.assertEqual(serialized, b"\x00\x64\x00\x20\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xc8")

    def test_deserialize_control(self):
        test_data = b"\x00\x64\x00\x20\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\xc8"
        m = netxms.Message.from_binary(test_data)
        self.assertTrue(m.control)
        self.assertFalse(m.binary)
        self.assertEqual(m.control_data, 200)

    def test_serialize_binary(self):
        m = netxms.Message(100)
        m.binary_data = b'12345678901234567890'
        self.assertEqual(m.flags, netxms.message.Flags.BINARY)
        serialized = m.serialize()
        self.assertEqual(serialized, b"\x00\x64\x00\x01\x00\x00\x00\x28\x00\x00\x00\x00\x00\x00\x00\x14\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x00\x00\x00\x00")
        m.binary_data = b'1234567890123456789'
        serialized = m.serialize()
        self.assertEqual(serialized, b"\x00\x64\x00\x01\x00\x00\x00\x28\x00\x00\x00\x00\x00\x00\x00\x13\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x00\x00\x00\x00\x00")
        m.binary_data = b'123456789012345678'
        serialized = m.serialize()
        self.assertEqual(serialized, b"\x00\x64\x00\x01\x00\x00\x00\x28\x00\x00\x00\x00\x00\x00\x00\x12\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36\x37\x38\x00\x00\x00\x00\x00\x00")

        # no padding
        m.binary_data = b'1234567890123456'
        serialized = m.serialize()
        self.assertEqual(serialized, b"\x00\x64\x00\x01\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x10\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36")

    def test_deserialize_binary(self):
        test_data = b"\x00\x64\x00\x01\x00\x00\x00\x28\x00\x00\x00\x00\x00\x00\x00\x14\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x00\x00\x00\x00"
        m = netxms.Message.from_binary(test_data)
        self.assertTrue(m.binary)
        self.assertFalse(m.control)
        self.assertEqual(m.binary_data, b'12345678901234567890')

    def test_serialize_field(self):
        test_data = b"\x00\x64\x00\x00\x00\x00\x00\x38\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x16\x00\x54\x00\x65\x00\x73\x00\x74\x00\x20\x00\x53\x00\x74\x00\x72\x00\x69\x00\x6e\x00\x67\x00\x00\x00\x00\x00\x00"
        test_data_no_padding = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x14\x00\x50\x00\x41\x00\x44\x00\x44\x00\x49\x00\x4e\x00\x47\x00\x50\x00\x41\x00\x44"
        test_data_unicode = b"\x00\x64\x00\x00\x00\x00\x00\x60\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x44\x04\x20\x04\x43\x04\x41\x04\x41\x04\x3a\x04\x38\x04\x39\x00\x20\x04\x22\x04\x35\x04\x3a\x04\x41\x04\x42\x00\x2c\x00\x20\x06\x27\x06\x44\x06\x46\x06\x35\x00\x20\x06\x28\x06\x27\x06\x44\x06\x44\x06\x3a\x06\x29\x00\x20\x06\x27\x06\x44\x06\x39\x06\x31\x06\x28\x06\x4a\x06\x29"
        test_data_binary = b"\x00\x64\x00\x00\x00\x00\x00\x28\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x04\x00\x00\x00\x00\x00\x00\x05\x01\x02\x03\x04\x05\x00\x00\x00\x00\x00\x00\x00"

        m = netxms.Message(100)
        m.message_id = 200
        m.set(300, "Test String")
        serialized = m.serialize()
        self.assertEqual(serialized, test_data)

        # test aligned message with zero padding 
        m = netxms.Message(100)
        m.message_id = 200
        m.set(300, "PADDINGPAD")
        serialized = m.serialize()
        self.assertEqual(serialized, test_data_no_padding)

        m = netxms.Message(100)
        m.message_id = 200
        m.set(300, "Русский Текст, النص باللغة العربية")
        serialized = m.serialize()
        self.assertEqual(serialized, test_data_unicode)

        m = netxms.Message(100, 200)
        m.set(300, b"\x01\x02\x03\x04\x05")
        serialized = m.serialize()
        self.assertEqual(serialized, test_data_binary)

    def test_deserialize_field(self):
        test_data = b"\x00\x64\x00\x00\x00\x00\x00\x38\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x16\x00\x54\x00\x65\x00\x73\x00\x74\x00\x20\x00\x53\x00\x74\x00\x72\x00\x69\x00\x6e\x00\x67\x00\x00\x00\x00\x00\x00"
        test_data_no_padding = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x14\x00\x50\x00\x41\x00\x44\x00\x44\x00\x49\x00\x4e\x00\x47\x00\x50\x00\x41\x00\x44"
        test_data_unicode = b"\x00\x64\x00\x00\x00\x00\x00\x60\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x44\x04\x20\x04\x43\x04\x41\x04\x41\x04\x3a\x04\x38\x04\x39\x00\x20\x04\x22\x04\x35\x04\x3a\x04\x41\x04\x42\x00\x2c\x00\x20\x06\x27\x06\x44\x06\x46\x06\x35\x00\x20\x06\x28\x06\x27\x06\x44\x06\x44\x06\x3a\x06\x29\x00\x20\x06\x27\x06\x44\x06\x39\x06\x31\x06\x28\x06\x4a\x06\x29"
        test_data_binary = b"\x00\x64\x00\x00\x00\x00\x00\x28\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x04\x00\x00\x00\x00\x00\x00\x05\x01\x02\x03\x04\x05\x00\x00\x00\x00\x00\x00\x00"

        m = netxms.Message.from_binary(test_data)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.STRING)
        self.assertEqual(f.value, "Test String")

        m = netxms.Message.from_binary(test_data_no_padding)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.STRING)
        self.assertEqual(f.value, "PADDINGPAD")

        m = netxms.Message.from_binary(test_data_unicode)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.STRING)
        self.assertEqual(f.value, "Русский Текст, النص باللغة العربية")

        m = netxms.Message.from_binary(test_data_binary)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.BINARY)
        self.assertEqual(f.value, b"\x01\x02\x03\x04\x05")
    
    def test_serialize_field_inetaddr(self):
        test_data_ipv4 = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x06\x00\x00\x00\x01\x02\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00"
        test_data_ipv6 = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x06\x00\x00\x00\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x80\x00\x00\x00\x00\x00\x00"

        m = netxms.Message(100, 200)
        m.set(300, ipaddress.IPv4Network('1.2.3.4/32'))
        serialized = m.serialize()
        self.assertEqual(serialized, test_data_ipv4)

        m = netxms.Message(100, 200)
        m.set(300, ipaddress.IPv6Network('2001:db8::1/128'))
        serialized = m.serialize()
        self.assertEqual(serialized, test_data_ipv6)

    def test_deserialize_field_inetaddr(self):
        test_data_ipv4 = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x06\x00\x00\x00\x01\x02\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00"
        test_data_ipv6 = b"\x00\x64\x00\x00\x00\x00\x00\x30\x00\x00\x00\xc8\x00\x00\x00\x01\x00\x00\x01\x2c\x06\x00\x00\x00\x20\x01\x0d\xb8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x80\x00\x00\x00\x00\x00\x00"

        m = netxms.Message.from_binary(test_data_ipv4)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.INETADDR)
        self.assertEqual(f.value, ipaddress.IPv4Network('1.2.3.4/32'))

        m = netxms.Message.from_binary(test_data_ipv6)
        self.assertEqual(m.message_code, 100)
        self.assertEqual(m.message_id, 200)
        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.INETADDR)
        self.assertEqual(f.value, ipaddress.IPv6Network('2001:db8::1/128'))

    def test_serialize_multuple_fields(self):
        test_data = b"\x00\x64\x00\x00\x00\x00\x00\x60\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x16\x00\x54\x00\x65\x00\x73\x00\x74\x00\x20\x00\x53\x00\x74\x00\x72\x00\x69\x00\x6e\x00\x67\x00\x00\x00\x00\x00\x00\x00\x00\x01\x2d\x03\x00\x03\xe8\x00\x00\x01\x2e\x00\x00\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x00\x00\x00\x01\x2f\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xea"

        m = netxms.Message(100)
        m.message_id = 200
        m.set(300, "Test String")
        m.set_int16(301, 1000)
        m.set(302, 1001)
        m.set_int64(303, 1002)

        serialized = m.serialize()
        self.assertEqual(serialized, test_data)

    def test_deserialize_multiple_fields(self):
        test_data = b"\x00\x64\x00\x00\x00\x00\x00\x60\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00\x01\x2c\x01\x00\x00\x00\x00\x00\x00\x16\x00\x54\x00\x65\x00\x73\x00\x74\x00\x20\x00\x53\x00\x74\x00\x72\x00\x69\x00\x6e\x00\x67\x00\x00\x00\x00\x00\x00\x00\x00\x01\x2d\x03\x00\x03\xe8\x00\x00\x01\x2e\x00\x00\x00\x00\x00\x00\x03\xe9\x00\x00\x00\x00\x00\x00\x01\x2f\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xea"
        m = netxms.Message.from_binary(test_data)

        f = m.get(300)
        self.assertEqual(f.field_id, 300)
        self.assertEqual(f.field_type, netxms.message.FieldType.STRING)
        self.assertEqual(f.value, "Test String")

        f = m.get(301)
        self.assertEqual(f.field_id, 301)
        self.assertEqual(f.field_type, netxms.message.FieldType.INT16)
        self.assertEqual(f.value, 1000)

        f = m.get(302)
        self.assertEqual(f.field_id, 302)
        self.assertEqual(f.field_type, netxms.message.FieldType.INTEGER)
        self.assertEqual(f.value, 1001)

        f = m.get(303)
        self.assertEqual(f.field_id, 303)
        self.assertEqual(f.field_type, netxms.message.FieldType.INT64)
        self.assertEqual(f.value, 1002)
