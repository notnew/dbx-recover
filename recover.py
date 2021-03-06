import sys
import os
from  struct import unpack

def main():
    if len(sys.argv) < 2:
        usage()
    filename = sys.argv[1]
    with open(filename, "rb") as file:
        print(file.read(4))
        dbx = DBX(file, os.path.getsize(filename))
        pos = dbx.next_obj()
        print("pos: {}".format(pos))
        pos = dbx.next_message()
        dbx.find_messages()
        print(len(dbx.start_segs))
        # print(dbx.map_segments())

class DBX(object):
    def __init__(self, file, size):
        self.file = file
        self.file_size = size
        self.start_segs = set()
        self.cont_segs = set()

    def find_messages(self):
        file = self.file
        pos = 0
        file.seek(pos)
        while pos < self.file_size:
            pos = self.next_message(pos=pos)
            if pos < 0:
                break
            if pos not in self.cont_segs:
                # print("walking {}".format(pos))
                for addr in self.map_segments(pos=pos):
                    self.cont_segs.add(addr)
                    if addr in self.start_segs:
                        self.start_segs.remove(addr)
                self.start_segs.add(pos)
            pos += 528

    def next_obj(self):
        """Return address of the next (likely) object; advance file there."""
        file = self.file
        pos = file.tell()
        assert pos % 4 == 0            # ensure we're aligned to a 4 byte word

        # 1st 4 bytes should also be the offset of the object in the file
        while int.from_bytes(file.read(4), 'little') != pos:
            if pos >= self.file_size:
                return -1
            pos += 4
        file.seek(pos)
        return pos

    def next_message(self, pos=None):
        """Return address of the next message segment object; advance file"""
        file = self.file
        if pos:
            file.seek(pos)

        # find next object that's an email segment
        while True:
            pos = self.next_obj()
            if pos < 0:
                return -1
            seg = MessageSegment(pos, file.read(16))
            if seg.is_valid():
                break
            file.seek(pos+4)
        file.seek(pos)
        return pos

    def read_message(self, pos=None):
        """Read the message from file, return the bytes"""
        def read_body(seg):
            return seg.read_body(self.file)
        return b''.join(self.map_segments(pos=pos, fn=read_body))

    def map_segments(self, pos=None, fn=lambda s: s.marker):
        """Visit each segment in the message, return a list of mapped segments

        The list contains the results of the function fn applied to each
        MessageSegment, or the MessageSegment's address if fn is None.

        args:
          fn = a function that takes a MessageSegment
        """
        file = self.file
        if pos:
            file.seek(pos)
        else:
            pos = file.tell()
        start = pos
        if not fn: fn = lambda s: s.marker

        result = []
        while True:
            seg = MessageSegment(pos, file.read(16))
            assert seg.is_valid()
            result.append(fn(seg))
            if seg.is_last():
                break
            pos = seg.next_addr
            file.seek(pos)
        return result

class MessageSegment(object):
    def __init__(self, address, data):
        (marker, body_len, msg_len, next_addr) = unpack("<4L", data)
        self.marker = marker
        self.body_len = body_len
        self.msg_len = msg_len
        self.next_addr = next_addr
        self.address = address
        self.body = None

    def __str__(self):
        return "<address: {}>  <marker: {}> <body_len: {}> <msg_len: {}> "\
               "<next_addr: {}>".format(self.address, self.marker,
                                        self.body_len, self.msg_len,
                                        self.next_addr)

    def is_valid(self):
        return (self.address == self.marker and self.body_len == 512 and
                self.msg_len <= 512)

    def is_last(self):
        """Return True if this is the last segment of a message"""
        return self.next_addr == 0

    def read_body(self, file):
        assert self.is_valid()
        file.seek(self.address + 16)
        self.body = file.read(self.msg_len)
        return self.body


def usage():
    print("Usage: {} <filename>".format(sys.argv[0]))
    exit()

if __name__ == "__main__":
    main()

