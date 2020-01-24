import struct

def anonymize_deltamed(file):
    with open(file, "r+b") as f:
        f.seek(290)
        while True:
            header = f.read(8)
            values = struct.unpack("II", header)
            if values[0] == 0xCAFD0301:
                # get pos
                pos = f.tell()
                patient = f.read(50)
                name = struct.unpack('50s', patient)
                #print name
                f.seek(pos)
                blank = [0] * 90
                f.write(struct.pack('B'*len(blank), *blank))
                f.flush()
                f.close()
                break
            if values[0] == 0xCAFD0300:
                continue
            if values[1]:
                f.read(values[1])

