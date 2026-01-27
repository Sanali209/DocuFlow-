import struct
import zlib

def create_png():
    width = 100
    height = 100

    # Header
    png = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr = b'IHDR' + struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(ihdr)
    png += struct.pack('!I', len(ihdr) - 4) + ihdr + struct.pack('!I', ihdr_crc)

    # IDAT (Red pixels)
    raw_data = b'\x00' + b'\xff\x00\x00' * width
    raw_data = raw_data * height
    compressed = zlib.compress(raw_data)
    idat = b'IDAT' + compressed
    idat_crc = zlib.crc32(idat)
    png += struct.pack('!I', len(idat) - 4) + idat + struct.pack('!I', idat_crc)

    # IEND
    iend = b'IEND'
    iend_crc = zlib.crc32(iend)
    png += struct.pack('!I', len(iend) - 4) + iend + struct.pack('!I', iend_crc)

    with open('verification/test_image.png', 'wb') as f:
        f.write(png)

if __name__ == "__main__":
    create_png()
