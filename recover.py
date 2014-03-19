import sys
from  struct import unpack

def main():
    if len(sys.argv) < 2:
        usage()
    filename = sys.argv[1]
    with open(filename, "rb") as file:
        print(file.read(4))
        dbx = DBX(file)
        pos = dbx.next_obj()
        print("pos: {}".format(pos))
        print("message:\n{}".format(dbx.next_message()))

class DBX(object):
    def __init__(self, file):
        self.file = file

    def next_obj(self):
        """Return address of the next (likely) object; advance file there."""
        file = self.file
        pos = file.tell()
        assert pos % 4 == 0            # ensure we're aligned to a 4 byte word

        # 1st 4 bytes should also be the offset of the object in the file
        while int.from_bytes(file.read(4), 'little') != pos:
            pos += 4
        file.seek(pos)
        return pos

    def next_message(self):
        """Return the next found message as a byte string"""

        file = self.file

        # find next object that's an email segment
        while True:
            pos = self.next_obj()
            seg = MessageSegment(pos, file.read(16))
            if seg.is_valid():
                break
            file.seek(pos+4)

        result = []
        while not seg.is_last():
            assert seg.is_valid()
            result.append(seg.read_body(file))
            file.seek(seg.next_addr)
            seg = MessageSegment(seg.next_addr, file.read(16))

        return b''.join(result)


class MessageSegment(object):
    def __init__(self, address, data):
        (marker, body_len, msg_len, next_addr) = unpack("<4L", data)
        self.marker = marker
        self.body_len = body_len
        self.msg_len = msg_len
        self.next_addr = next_addr
        self.address = address

    def is_valid(self):
        return (self.address == self.marker and self.body_len == 512 and
                self.msg_len <= 512)

    def is_last(self):
        """Return True if this is the last segment of a message"""
        return self.msg_len < 512

    def read_body(self, file):
        assert self.is_valid()
        file.seek(self.address + 16)
        return file.read(self.msg_len)


def usage():
    print("Usage: {} <filename>".format(sys.argv[0]))
    exit()

if __name__ == "__main__":
    main()

