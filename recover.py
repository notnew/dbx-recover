import sys

def main():
    if len(sys.argv) < 2:
        usage()
    filename = sys.argv[1]
    file = open(filename, "rb")
    print(file.read(4))
    pos = find_obj(file)
    print("pos: %s" % pos)
    file.close()

# Find a (likely) object in the dbx
# where the 1st 4 bytes of the object are the offset of the object in the file
def find_obj(file):
    pos = file.tell()
    if pos % 4 != 0:            # ensure we're aligned to a 4 byte word
        pos = (1 + pos // 4) * 4
        file.seek(pos)
    while (int.from_bytes(file.read(4), 'little') != pos):
        pos += 4
        if pos > 100000:
            break
    return pos

def usage():
    print("Usage: %s <filename>" % sys.argv[0])
    exit()

if __name__ == "__main__":
    main()

