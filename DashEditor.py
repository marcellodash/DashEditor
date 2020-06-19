#!/usr/bin/env python3

import sys
from Formats.BIN import *
from Formats.MSG import do_extract_msg, do_insert_msg
from Formats.TIM import do_extract_tim, do_insert_tim
from Formats.FONT import do_extract_font, do_insert_font

help_msg = (
    """\nDashEditor v0.9 - Mega Man Legends Translation Toolkit
Created by _Ombra_ of SadNES cITy Translations
Website: http://www.sadnescity.it\n
DashEditor.py [option] [file_or_folder]\n
  -e   extracts che content of BIN file.
  -i   inserts an extracted folder to BIN file.\n""")

# Check if 2 arguments are passed
if len(sys.argv) != 3:
    print("{}\nOne or more arguments missing or too many".format(help_msg))
# If they are, check if the command argument is valid
elif not any(cmd in sys.argv[1] for cmd in ("-e", "-i")):
    print("{}\nInvalid command!".format(help_msg))
# If the command argument is valid, check if file exists and open it
elif not os.path.exists(sys.argv[2]):
    print("\nFile or folder not found")
# If second argument is -e and third argument is file
elif sys.argv[1] == "-e" and not os.path.isfile(sys.argv[2]):
    print("\nExpected file. Provided folder")
elif sys.argv[1] == "-i" and not os.path.isdir(sys.argv[2]):
    print("\nExpected folder. Provided file")
else:
    # Ex: TEST/TEST2/FILE.BIN or TEST/TEST2
    full_file_or_folder_name: str = sys.argv[2].replace("\\", "/")
    # Get only the paths from the normalized path
    # Ex: TEST/TEST2/FILE.BIN == TEST/TEST2/FILE
    full_path_and_file_no_ext = os.path.splitext(full_file_or_folder_name)[0]
    # Get only the file name from the normalized path
    # Ex: TEST/TEST2/FILE.BIN == FILE.BIN
    file_name_only = os.path.basename(full_file_or_folder_name)

    # Full path to the index file
    # Ex: TEST/TEST2/TEST2.BIN == TEST/TEST2/TEST2.txt
    index_file_path = "{}/{}.txt".format(full_path_and_file_no_ext, file_name_only.replace(".BIN", ""))

    if sys.argv[1] == "-e" and os.path.isfile(sys.argv[2]):
        file_data = open(full_file_or_folder_name, "rb").read()

        # Check if the file is a valid MML BIN file
        try:
            assert file_data[64:67].decode() == "..\\"
        except AssertionError:
            print("\nNot a valid MML PSX BIN file")
        else:

            # Create index file
            if not os.path.exists(full_path_and_file_no_ext):
                os.mkdir(full_path_and_file_no_ext)

            index_file = open(index_file_path, "w+")

            # Proceed with extraction
            do_unpack_bin(full_path_and_file_no_ext, file_data, index_file)

            index_file.seek(0)
            index_file_content = index_file.read().splitlines()
            index_file_line = 0

            while index_file_line < len(index_file_content):
                file_name = index_file_content[index_file_line].split(",")[0]
                file_path = index_file_path.replace(os.path.basename(index_file_path), "") + file_name
                # If MSG files are found, extract them
                if any(fn in index_file_content[index_file_line].upper() for fn in [".MSG"]):
                    do_extract_msg(file_path)
                    index_file_content = index_file_content.pop(0)
                    index_file_line += 1
                # If TIM files are found, extract them
                elif any(fn in index_file_content[index_file_line].upper() for fn in [".TIM"]):
                    do_extract_tim(file_path)
                    index_file_line += 1
                # If FONT files are found, extract them
                elif any(fn in index_file_content[index_file_line].upper() for fn in ("FONT.DAT", "KAIFONT.DAT")):
                    do_extract_font(file_path)
                    index_file_line += 1
                else:
                    index_file_line += 1

            # Close the index file and return
            index_file.close()

    # If argument is -i, pack BIN files
    elif sys.argv[1] == "-i" and os.path.isdir(sys.argv[2]):

        if not os.path.exists(index_file_path):
            print("\nIndex file missing")
        elif os.path.exists("{}.BIN".format(full_file_or_folder_name)):
            print("\nBIN file already exists. Please delete or move/delete before creation.")
        else:
            index_file_content = open(index_file_path, "r").readlines()

            index_file_line = 0

            while index_file_line < len(index_file_content):
                file_name = index_file_content[index_file_line].split(",")[0].upper()

                # If any MSG file is found. Insert TXT into MSG
                if any(fn in index_file_content[index_file_line].upper() for fn in [".MSG"]):
                    original_msg = (index_file_path.replace(os.path.basename(index_file_path), "") + file_name)
                    text_file = (index_file_path.replace(os.path.basename(index_file_path), "") + file_name + ".txt")
                    if os.path.exists(original_msg) and os.path.exists(text_file):
                        do_insert_msg(original_msg, text_file)
                    index_file_line += 1
                # If any TIM file is found. Insert TIM into original TIM
                elif any(fn in index_file_content[index_file_line].upper() for fn in [".TIM"]):
                    original_tim = (index_file_path.replace(os.path.basename(index_file_path), "") + file_name)
                    edited_tim = (index_file_path.replace(os.path.basename(index_file_path), "")
                                  + file_name.replace(".TIM", "_EXT.TIM"))
                    if os.path.exists(original_tim) and os.path.exists(edited_tim):
                        do_insert_tim(original_tim, edited_tim)
                    index_file_line += 1
                # If FONT file is found. Insert FONT into original FONT
                elif any(fn in index_file_content[index_file_line].upper() for fn in ("FONT.DAT", "KAIFONT.DAT")):
                    original_font = (index_file_path.replace(os.path.basename(index_file_path), "") + file_name)
                    edited_font = (index_file_path.replace(os.path.basename(index_file_path), "")
                                   + file_name.replace(".DAT", ".TIM"))
                    if os.path.exists(original_font) and os.path.exists(edited_font):
                        do_insert_font(original_font, edited_font)
                    index_file_line += 1
                # Else insert as is
                else:
                    index_file_line += 1

            do_pack_bin(full_file_or_folder_name, index_file_content)
