#!/usr/bin/env python3
# Inspired by: https://www.youtube.com/watch?v=izG7qT0EpBw
# The CRC values are verified using: https://crccalc.com/
# https://gist.github.com/Lauszus/6c787a3bc26fea6e842dfb8296ebd630

def reflect_data(x, width):
    # See: https://stackoverflow.com/a/20918545
    if width == 8:
        x = ((x & 0x55) << 1) | ((x & 0xAA) >> 1)
        x = ((x & 0x33) << 2) | ((x & 0xCC) >> 2)
        x = ((x & 0x0F) << 4) | ((x & 0xF0) >> 4)
    elif width == 16:
        x = ((x & 0x5555) << 1) | ((x & 0xAAAA) >> 1)
        x = ((x & 0x3333) << 2) | ((x & 0xCCCC) >> 2)
        x = ((x & 0x0F0F) << 4) | ((x & 0xF0F0) >> 4)
        x = ((x & 0x00FF) << 8) | ((x & 0xFF00) >> 8)
    elif width == 32:
        x = ((x & 0x55555555) << 1) | ((x & 0xAAAAAAAA) >> 1)
        x = ((x & 0x33333333) << 2) | ((x & 0xCCCCCCCC) >> 2)
        x = ((x & 0x0F0F0F0F) << 4) | ((x & 0xF0F0F0F0) >> 4)
        x = ((x & 0x00FF00FF) << 8) | ((x & 0xFF00FF00) >> 8)
        x = ((x & 0x0000FFFF) << 16) | ((x & 0xFFFF0000) >> 16)
    else:
        raise ValueError('Unsupported width')
    return x

def crc_poly(data, n, poly, crc=0, ref_in=False, ref_out=False, xor_out=0):
    g = 1 << n | poly  # Generator polynomial

    # Loop over the data
    for d in data:
        # Reverse the input byte if the flag is true
        if ref_in:
            d = reflect_data(d, 8)

        # XOR the top byte in the CRC with the input byte
        crc ^= d << (n - 8)

        # Loop over all the bits in the byte
        for _ in range(8):
            # Start by shifting the CRC, so we can check for the top bit
            crc <<= 1

            # XOR the CRC if the top bit is 1
            if crc & (1 << n):
                crc ^= g

    # Reverse the output if the flag is true
    if ref_out:
        crc = reflect_data(crc, n)

    # Return the CRC value
    return crc ^ xor_out


def crc8(msg):
    # CRC-8
    crc = crc_poly(msg, 8, 0x07)
    return hex(crc)

def crc8_itu(msg):
    # CRC-8/ITU
    crc = crc_poly(msg, 8, 0x07, xor_out=0x55)
    return hex(crc)

def crc8_darc(msg):
    # CRC-8/DARC
    crc = crc_poly(msg, 8, 0x39, ref_in=True, ref_out=True)
    return hex(crc)

def crc16_xmodem(msg):
    # CRC-16/XMODEM
    crc = crc_poly(msg, 16, 0x1021)
    return hex(crc)

def crc16_maxim(msg):
    # CRC-16/MAXIM
    crc = crc_poly(msg, 16, 0x8005, ref_in=True, ref_out=True, xor_out=0xFFFF)
    return hex(crc)

def crc16_usb(msg):
    # CRC-16/USB
    crc = crc_poly(msg, 16, 0x8005, crc=0xFFFF, ref_in=True, ref_out=True, xor_out=0xFFFF)
    return hex(crc)

def crc32_bzip2(msg):
    # CRC-32/BZIP2
    crc = crc_poly(msg, 32, 0x04C11DB7, crc=0xFFFFFFFF, xor_out=0xFFFFFFFF)
    return hex(crc)

def crc32(msg):
    # CRC-32C
    crc = crc_poly(msg, 32, 0x1EDC6F41, crc=0xFFFFFFFF, ref_in=True, ref_out=True, xor_out=0xFFFFFFFF)
    return hex(crc)

def crc32_xfer(msg):
    # CRC-32/XFER
    crc = crc_poly(msg, 32, 0x000000AF)
    return hex(crc)

def crc32_mpeg2(msg):
    # CRC-32/MPEG-2
    crc = crc_poly(msg, 32, 0x04C11DB7, crc=0xFFFFFFFF)
    return hex(crc)
