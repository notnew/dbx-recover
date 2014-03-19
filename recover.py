import sys
import struct

def main():
    if len(sys.argv) < 2:
        usage()
    filename = sys.argv[1]
    with open(filename, "rb") as file:
        print(file.read(4))
        pos = find_obj(file)
        print("pos: %s" % pos)

def find_obj(file):
    """Return the address of the next (likely) object; advance file there.

    The 1st 4 bytes of the object should be the offset of the object in the file
    """
    pos = file.tell()
    assert(pos % 4 == 0)            # ensure we're aligned to a 4 byte word

    while (int.from_bytes(file.read(4), 'little') != pos):
        pos += 4
    file.seek(pos)
    return pos

def usage():
    print("Usage: {} <filename>".format(sys.argv[0]))
    exit()

if __name__ == "__main__":
    main()

