r"""
SOOD messages consists of a header and a list of properties encoded as key/value pairs.

The header starts with "SOOD", followed by a byte with the value 2, followed by a byte representing the type.
The type is either 'Q' for "Query" or # 'R' for "Response.
The key/value pairs follows directly after the type.
The keys and values are prepended with one or two bytes with length info. One byte for keys,
two bytes for values.
In other words:
SOOD\x02<onelettertype><1bytelen><key><2bytelen><value><1bytelen><key><2bytelen><value>...

All lengths are big-endian.

The service_id always has the value 00720724-5143-4a9b-abac-0e50cba674bb

Query format:
SOOD\x02Q<1bytelen>query_service_id<2bytelen>00720724-5143-4a9b-abac-0e50cba674bb<1bytelen>_tid<2bytelen><the_tid>

Response format:
SOOD\x02R<1bytelen>name<2bytelen><the_name><1bytelen>display_version<2bytelen><the_version><1bytelen>unique_id<2bytelen><the_id><1bytelen>service_id<twobytelen>00720724-5143-4a9b-abac-0e50cba674bb<1bytelen>tcp_port<twobytelen><the_port><1bytelen>http_port<twobytelen><the_port><1bytelen>_tid<twobytelen>c64e3888-f2f2-4c4a-9f89-2093ae4217a6
"""
import re


# import enum
# from itertools import count
# def auto(it=count()):
#   return next(it)
# enum.auto = auto
# from enum import Enum, auto


class FormatException(Exception):
    """Exception to be raised on errors in a binary SOOD message."""

    def __init__(self, message):
        """Init with the message that causes the error."""
        #Exception.__init__()
        self.message = message


class SOODMessage:  # pylint: disable=too-few-public-methods
    """Class for parsing SOOD messages."""

    __MESSAGE_PREFIX__ = b"SOOD\x02"

    class SOODMessageType:
        """Symbolic names for the message types."""

        # QUERY = auto()
        # RESPONSE = auto()
        class QUERY:
            pass

        class RESPONSE:
            pass

        def __repr__(self):
            """Print class and name."""
            return "%s, %s" % (self.__class__.__name__, self.name)
            #return f"<{self.__class__.__name__}, {self.name}>"

    def __init__(self, message):
        """Init with the message to parse."""
        if not message.startswith(self.__MESSAGE_PREFIX__):
            raise FormatException("Error in message header")
        self._message = message
        self._current_position = len(self.__MESSAGE_PREFIX__)

    def _parse_property(self, size_of_size):
        length = int(
            self._message[
                self._current_position : self._current_position + size_of_size
            ].encode('hex'), 32
        )
        self._current_position += size_of_size
        if self._current_position + length > len(self._message):
            return None
        part_string = self._message[
            self._current_position : self._current_position + length
        ].decode()
        self._current_position += len(part_string)
        return part_string

    def _parse_message_properties(self, message):
        print(message)
        # message = message.replace('\x0f', '\x04')
        servers = message.split('\x02')
        server1 = servers[1]
        serverprops = ''
        # serverpropsclean = re.sub(r'[^\x00-\x7f]' ,'?', serverprops[1])
        for s in server1:
            if ord(s) < 127 and ord(s) > 31:
                serverprops += s
            else:
                serverprops += '\x00'
        serverprops = serverprops.replace('\x00\x00', '\x00').split('\x00')
        serverprops.pop(0)
        properties = {}
        looprange = len(serverprops)/2
        for x in range(looprange):
            key = serverprops[2*x]
            value = serverprops[2*x+1]
            properties[key] = value
        return properties


    def _parse_properties(self):
        properties = {}
        properties = self._parse_message_properties(self._message)
        # while self._current_position < len(self._message):
        #     part_key = self._parse_property(1)
        #     if part_key is None:
        #         return None
        #     part_value = self._parse_property(2)
        #     if part_value is None:
        #         return None
        #     properties[part_key] = part_value
        return properties

    def _parse_type(self):
        type_letter = self._message[self._current_position].upper()
        self._current_position += 1
        if type_letter not in ["Q", "R"]:
            return None
        return (
            self.SOODMessageType.QUERY
            if type_letter == "Q"
            else self.SOODMessageType.RESPONSE
        )

    @property
    def as_dictionary(self):
        """Expose the message as a dictionary."""
        message_type = self._parse_type()
        if message_type is None:
            raise FormatException("Error in message type")

        message_properties = self._parse_properties()
        if message_properties is None:
            raise FormatException("Error in property")

        message = {
            "type": message_type,
            "properties": message_properties,
        }
        return message
