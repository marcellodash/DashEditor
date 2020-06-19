#!/usr/bin/env python3

import re
import os

from Formats.BIN import bytes_to_uint, uint_to_bytes, ulong_to_bytes

header = 2048  # 0x800

char_table = {
    # FONT TABLE
    # Numbers
    0x00: '0', 0x01: '1', 0x02: '2', 0x03: '3', 0x04: '4', 0x05: '5', 0x06: '6',
    0x07: '7', 0x08: '8', 0x09: '9',
    # Symbols
    0x0A: 'ç', 0x0B: 'ß', 0x0C: '\'', 0x0D: '!', 0x0E: '?',
    0x0F: '<LCORNER>', 0x10: '<DOT>', 0x11: '(', 0x12: ')', 0x13: ':',
    # Letters
    0x15: 'A', 0x16: 'B', 0x17: 'C', 0x18: 'D', 0x19: 'E', 0x1A: 'F', 0x1B: 'G', 0x1C: 'H',
    0x1D: 'I', 0x1E: 'J', 0x1F: 'K', 0x20: 'L', 0x21: 'M', 0x22: 'N', 0x23: 'O', 0x24: 'P',
    0x25: 'Q', 0x26: 'R', 0x27: 'S', 0x28: 'T', 0x2A: 'U', 0x2B: 'V', 0x2C: 'W', 0x2D: 'X',
    0x2E: 'Y', 0x2F: 'Z', 0x30: 'a', 0x31: 'b', 0x32: 'c', 0x33: 'd', 0x34: 'e', 0x35: 'f',
    0x36: 'g', 0x37: 'h', 0x38: 'i', 0x39: 'j', 0x3A: 'k', 0x3B: 'l', 0x3C: 'm', 0x3D: 'n',
    0x3F: 'o', 0x40: 'p', 0x41: 'q', 0x42: 'r', 0x43: 's', 0x44: 't', 0x45: 'u', 0x46: 'v',
    0x47: 'w', 0x48: 'x', 0x49: 'y', 0x4A: 'z',
    # Symbols
    0x4B: '&', 0x4C: '<ZAIRE>', 0x4D: '<YEN>', 0x4E: '/', 0x4F: ' ', 0x50: '<RCORNER>', 0x51: '~',
    0x52: '-',
    # Buttons
    0x54: '<CIRCLE>', 0x55: '<TRIANGLE>', 0x56: '<CROSS>', 0x57: '<SQUARE>',
    0x58: '<L1>', 0x59: '<L2>', 0x5A: '<R1>', 0x5B: '<R2>',
    # Other Symbols
    0x5C: ',', 0x5D: '\\', 0x5E: '.', 0x5F: '<...>', 0x60: '<HAND>', 0x61: '+', 0x62: '%',
    # Letters with accents
    0x63: 'Ä', 0x64: 'À', 0x65: 'Â', 0x66: 'È', 0x67: 'Ê', 0x69: 'É', 0x6A: 'Ï', 0x6B: 'Ì',
    0x6C: 'Ö', 0x6D: 'Ô', 0x6E: 'Ü', 0x6F: 'Ù', 0x70: 'Û', 0x71: 'Ç', 0x72: 'ä',
    0x73: 'à', 0x74: 'â', 0x75: 'è', 0x76: 'ê', 0x77: 'é', 0x78: 'ï', 0x79: 'î',
    0x7A: 'ö', 0x7B: 'ô', 0x7C: 'ü', 0x7E: 'ù', 0x7F: 'û',
    0x80: '<ALPHA>', 0x81: '<OMEGA>', 0x82: ';', 0x83: '=',
    # NOT IN TABLE
    0x86: '\n'
}


def tag_args(full_tag: str, typ: str) -> list:
    i = 0
    tag_arguments: list = []
    if typ == "S":
        tag_arguments = re.findall(r"\s([^\W]*)", full_tag)
        tag_arguments = re.findall(r'.{1,2}', tag_arguments[i])
    elif typ == "M":
        tag_arguments = re.findall(r"=([^\W]*)", full_tag)
    return tag_arguments


def do_encode_text_block(text_block):
    # Invert character table Dictionary
    inverse_char_table = {v: k for k, v in char_table.items()}

    output = []
    bi = 0

    # Analyze block and convert
    while bi < len(text_block):
        c = text_block[bi]
        # If char is not < then read from table and write to output
        if c != '<':
            output.append(inverse_char_table[c])
            bi += 1
            continue

        # If char is < read until > is found and define the tag for conversion
        tag_end = text_block.find('>', bi + 1)
        tag = text_block[bi + 1:tag_end]

        ai = 0

        # Check which tag and convert
        if "<{}>".format(tag) in inverse_char_table:
            output.append(inverse_char_table["<{}>".format(tag)])

        elif tag.startswith('PAUSE'):
            output.append(0x8B)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('UNK1') and tag.endswith('FF'):
            output.append(0x8A)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('UNK2'):
            output.append(0x8A)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('MENU'):
            output.append(0x8C)
            for arg in tag_args(tag, typ="M"):
                if len(arg) == 4:
                    args = arg[ai:ai + 4]
                    output.extend((int(args, 16) & 0xFF, int(args, 16) >> 8))
                elif len(arg) == 2:
                    output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('UNK3'):
            output.append(0x8E)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('AUDIO'):
            output.append(0x8F)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('COLOR'):
            output.append(0x89)
            output.append(int(tag_args(tag, typ="S")[0], 16))

        elif tag.startswith('UNK4'):
            output.append(0x93)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('SEL'):
            output.append(0x96)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('JMP'):
            output.append(0x99)
            for arg in tag_args(tag, typ="S"):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('UNK5'):
            output.append(0x9A)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('UNK6'):
            output.append(0x9B)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('MSG_ID'):
            output.append(0x9C)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('WIN_SUB'):
            output.append(0x9F)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('PAD'):
            output.append(0xA0)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('WIN_MAIN_1 T=8C'):
            output.append(0xA1)
            for arg in tag_args(tag, typ="M"):
                if len(arg) == 4:
                    args = arg[ai:ai + 4]
                    output.extend((int(args, 16) & 0xFF, int(args, 16) >> 8))
                elif len(arg) == 2:
                    output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('WIN_MAIN_1 T=94'):
            output.append(0xA1)
            for arg in tag_args(tag, typ="M"):
                if len(arg) == 4:
                    args = arg[ai:ai + 4]
                    output.extend((int(args, 16) & 0xFF, int(args, 16) >> 8))
                elif len(arg) == 2:
                    output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('WIN_MAIN_2'):
            output.append(0xA2)
            for arg in tag_args(tag, typ="M"):
                if len(arg) == 4:
                    args = arg[ai:ai + 4]
                    output.extend((int(args, 16) & 0xFF, int(args, 16) >> 8))
                elif len(arg) == 2:
                    output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('WAIT'):
            output.append(0xA4)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))
            bi += 1  # Account for the extra \n

        elif tag.startswith('CLOSE'):
            output.append(0xA9)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('PRICE_ZAIRE'):
            output.extend((0xBA, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F))

        elif tag.startswith('ITEM'):
            output.append(0xD0)
            for arg in reversed(tag_args(tag, typ="S")):
                output.append(int(arg[ai:], 16))

        elif tag.startswith('PRICE_ZENNY'):
            output.extend((0xD3, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F))

        else:
            output.append(int(tag, 16))

        bi += len(tag) + 2

    return output


def do_insert_msg(original_msg, text_file):
    print("\nInserting {}".format(original_msg))
    # Open TXT file
    text = open(text_file, "r").read()

    # Open MSG file
    msg_file = open(original_msg, "rb+")
    # Read the actual file size
    msg_file.seek(4)
    file_size = bytes_to_uint(msg_file.read(4))

    # Read pointer table size
    msg_file.seek(header)
    ptr_tbl_size = bytes_to_uint(msg_file.read(2))
    ptr_table: list = [ptr_tbl_size]

    print("Pointer table size is {} blocks ({} bytes)".format(ptr_tbl_size // 2, ptr_tbl_size))

    i = 0
    current_block = 1
    encoded_block: list = []

    while i < len(text):
        # Skip the [Blocks] text but separate them for recalculating pointers
        c = text[i]

        if c == '[':
            # Find the end of the textual Block info and start of next
            block_end = text.find(']', i + 1)
            next_block_start = text.find('[', i + 1)

            # If there is no more blocks after, read until the end of the file
            if next_block_start == -1:
                text_block = text[block_end + 2:-2]
            # If there is another block after, read until the beginning of the next block
            else:
                text_block = text[block_end + 2:next_block_start - 2]  # Remove the \n\n at beginning and end of block

            # Encode text block to list of bytes
            encoded_text_block = do_encode_text_block(text_block)
            encoded_block.append(encoded_text_block)

            if current_block != ptr_tbl_size // 2:
                # Append the size of the encoded block to the pointer table
                ptr_table.append(ptr_table[-1] + len(encoded_text_block))
                current_block += 1

        i += 1

    # Convert pointer table int to sequence of bytes
    ptr_table_bytes: bytes = b''
    for items in ptr_table:
        if not items == file_size:
            ptr_table_bytes += (uint_to_bytes(items))

    # Convert list of lists of encoded blocks to bytes
    encoded_block_bytes = bytes([val for sublist in encoded_block for val in sublist])
    print("Encoded text data size is {} bytes".format(len(encoded_block_bytes)))

    # Get size of file
    msg_file_size = msg_file.seek(0, os.SEEK_END)
    # Get size of new file
    new_file_size = header + len(ptr_table_bytes) + len(encoded_block_bytes)

    # Check if the new size is within the limits. Else throw and exception
    if new_file_size > msg_file_size:
        print("ERROR: New MSG file is {} bytes. Size limit is {} bytes.".format(new_file_size, msg_file_size))
        exit()
    else:
        # Write new data to the MSG file
        msg_file.seek(header)
        msg_file.write(ptr_table_bytes + encoded_block_bytes)
        # Get offset after writing pointer table and encoded text
        current_offset = msg_file.tell()
        # Write the new file size to the header
        msg_file.seek(4)
        msg_file.write(ulong_to_bytes(current_offset - header))
        msg_file.seek(current_offset)
        msg_file.seek(current_offset)

        # Fill the rest of the file with 00
        while current_offset < msg_file_size:
            msg_file.write(b'\x00')
            current_offset += 1

    msg_file.close()


def do_decode_block(block_data):
    decoded_block = ''
    i = 0
    while i < len(block_data):
        b1 = block_data[i]
        b2 = block_data[i + 1] if i + 1 < len(block_data) else None
        b3 = block_data[i + 2] if i + 2 < len(block_data) else None
        b4 = block_data[i + 3] if i + 3 < len(block_data) else None
        b5 = block_data[i + 4] if i + 4 < len(block_data) else None
        b6 = block_data[i + 5] if i + 5 < len(block_data) else None
        b7 = block_data[i + 6] if i + 6 < len(block_data) else None
        b8 = block_data[i + 7] if i + 7 < len(block_data) else None
        b9 = block_data[i + 8] if i + 8 < len(block_data) else None
        b10 = block_data[i + 9] if i + 9 < len(block_data) else None
        b11 = block_data[i + 10] if i + 10 < len(block_data) else None
        b12 = block_data[i + 11] if i + 11 < len(block_data) else None
        b13 = block_data[i + 12] if i + 12 < len(block_data) else None

        try:
            decoded_block += char_table[b1]
        except KeyError:
            if b1 == 0x8B:  # TODO: Verify in game
                decoded_block += '<PAUSE {:02X}{:02X}>\n'.format(b3, b2)
                i += 2
            elif (b1, b7) == (0x8A, 0xFF):  # TODO: Verify in game
                decoded_block += \
                    '<UNK1 {:02X}{:02X}{:02X}{:02X}{:02X}{:02X}>\n'.format(b2, b3, b4, b5, b6, b7)
                i += 6
            elif b1 == 0x8A:  # TODO: Verify in game
                decoded_block += '<UNK2 {:02X}{:02X}>'.format(b2, b3)
                i += 2
            elif b1 == 0x8C:  # TODO: Verify in game
                decoded_block += \
                    '<MENU PX={:02X}{:02X} PY={:02X}{:02X} SX={:02X} SY={:02X}' \
                    ' ?={:02X} WAT={:02X} BORDER={:02X}>' \
                    '\n'.format(b3, b2, b5, b4, b6, b7, b8, b9, b10)
                i += 9
            elif b1 == 0x8E:  # TODO: Verify in game
                decoded_block += '<UNK3 {:02X}{:02X}>'.format(b2, b3)
                i += 2
            elif b1 == 0x8F:
                decoded_block += '<AUDIO {:02X}{:02X}{:02X}{:02X}>\n'.format(b5, b4, b3, b2)
                i += 4
            elif b1 == 0x89:  # 00 = White, 02 = Red, 04 = Blue, 05 = Purple
                decoded_block += '<COLOR {:02X}>'.format(b2)
                i += 1
            elif b1 == 0x93:  # TODO: Verify in game
                decoded_block += '<UNK4 {:02X}{:02X}>'.format(b2, b3)
                i += 2
            elif b1 == 0x96:
                decoded_block += '<SEL {:02X}{:02X}>'.format(b2, b3)
                i += 2
            elif b1 == 0x99:  # TODO: Verify in game
                decoded_block += '<JMP {:02X}{:02X}>'.format(b2, b3)
                i += 2
            elif b1 == 0x9A:  # TODO: Verify in game
                decoded_block += '<UNK5 {:02X}{:02X}>'.format(b3, b2)
                i += 2
            elif b1 == 0x9B:  # TODO: Verify in game
                decoded_block += '<UNK6 {:02X}{:02X}>'.format(b3, b2)
                i += 2
            elif b1 == 0x9C:  # TODO: Verify in game
                decoded_block += '<MSG_ID {:02X}{:02X}>'.format(b3, b2)
                i += 2
            elif b1 == 0x9F:
                decoded_block += '<WIN_SUB {:02X}{:02X}{:02X}>\n'.format(b4, b3, b2)
                i += 3
            elif b1 == 0xA0:
                decoded_block += '<PAD {:02X}{:02X}>'.format(b3, b2)
                i += 2
            elif (b1, b2) == (0xA1, 0x8C):
                decoded_block += \
                    '<WIN_MAIN_1 T={:02X} PX={:02X}{:02X} PY={:02X}{:02X} SX={:02X} SY={:02X}' \
                    ' ?={:02X} WAT={:02X} BORDER={:02X}>' \
                    '\n'.format(b2, b4, b3, b6, b5, b7, b8, b9, b10, b11)
                i += 10
            elif (b1, b2) == (0xA1, 0x94):
                decoded_block += \
                    '<WIN_MAIN_1 T={:2X} ?={:02X} PX={:02X}{:02X} PY={:02X}{:02X} SX={:02X} SY={:02X}' \
                    ' ?={:02X} WAT={:02X} BORDER={:02X}>' \
                    '\n'.format(b2, b3, b5, b4, b7, b6, b8, b9, b10, b11, b12)
                i += 11
            elif (b1, b2) == (0xA2, 0x94):
                decoded_block += \
                    '<WIN_MAIN_2 T={:2X} PX={:02X}{:02X} PY={:02X}{:02X} SX={:02X} SY={:02X}' \
                    ' ?={:02X} WAT={:02X} BORDER={:02X}>' \
                    '\n'.format(b2, b4, b3, b6, b5, b7, b8, b9, b10, b11)
                i += 10
            elif b1 == 0xA4:
                decoded_block += '<WAIT {:02X}{:02X}>\n'.format(b3, b2)
                i += 2
            elif b1 == 0xA9:
                decoded_block += '<CLOSE {:02X}{:02X}{:02X}{:02X}{:02X}>'.format(b6, b5, b4, b3, b2)
                i += 5
            elif (b1, b2, b3, b4, b5, b6, b7) == (
                    0xBA, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F):  # TODO: Verify in game
                decoded_block += '<PRICE_ZAIRE>'
                i += 6
            elif b1 == 0xD0:  # TODO: Verify in game
                decoded_block += '<ITEM {:02X}{:02X}{:02X}{:02X}>'.format(b5, b4, b3, b2)
                i += 4
            elif (b1, b2, b3, b4, b5, b6, b7) == (
                    0xD3, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F, 0x4F):  # TODO: Verify in game
                decoded_block += '<PRICE_ZENNY>'
                i += 6
            else:
                decoded_block += '<{:02X}>'.format(b1)
        i += 1

    return decoded_block


def do_extract_msg(file_path):
    print("\nExtracting {}".format(file_path))
    # Open MSG file
    msg_file = open(file_path, "rb").read()
    # Read the actual file size
    file_size = bytes_to_uint(msg_file[4:8])
    # Read pointer table size
    ptr_tbl_size = bytes_to_uint(msg_file[header:header + 2])
    # Read pointer table data
    ptr_tbl_data = msg_file[header:header + ptr_tbl_size]

    print("Pointer table contains {} blocks".format(int(ptr_tbl_size // 2)))

    output_file = open(file_path + ".txt", "w")

    ptr_tbl_offset = 0
    block_number = 1

    while ptr_tbl_offset < ptr_tbl_size:
        block_start_offset = header + bytes_to_uint(ptr_tbl_data[ptr_tbl_offset:ptr_tbl_offset + 2])
        block_end_offset = header + bytes_to_uint(ptr_tbl_data[ptr_tbl_offset + 2:ptr_tbl_offset + 4])
        # If we reached the end of the offset table, use the file size for the last bank
        if block_end_offset == 2048:
            block_end_offset = header + file_size

        block_data = msg_file[block_start_offset:block_end_offset]

        # Write each block with offset information
        output_file.write(
            "[Block {}, String: {:04X}-{:04X}]\n".format(block_number, block_start_offset, block_end_offset)
        )

        output_file.write(do_decode_block(block_data) + "\n\n")

        ptr_tbl_offset += 2
        block_number += 1

    output_file.close()
