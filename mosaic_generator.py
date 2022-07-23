#!/usr/bin/env python3

# Built in libraries
import os
import subprocess
import requests
import shutil
import json
import sys
from datetime import datetime
from random import choice
from multiprocessing import Pool, cpu_count
# Adds ability to pool.map to use functions with multiple arguments
from functools import partial

# Add in libraries
# Python Imaging Library (PIL) image processing package for Python language.
from PIL import Image


# Value to input into equations to calculate the number of tiles
# Percentage of image width
tile_percentage_num = .015


def create_dict_resize_save_tiles(size, pathname):
    """
    Resizes tiles, gets the rgb and saves to dict.
    Saves file to new directory.
    """



    # Resizes tiles and saves to a directory
    tile_dict = {}
    for file in os.listdir(pathname):
        filename = os.path.join(pathname, file)
        with Image.open(filename).convert("RGB") as im:
            im1 = im.resize(size)
            # Get image average RGB while file is open, add to dictionary
            if filename not in tile_dict:
                tile_dict[file] = get_rgb(im1)
            # Save tile to new directory
            im1.save(os.path.join(tile_dir, file), "JPEG")

    # Save tile_dict to json file
    json_filename = os.path.basename(pathname).split(".")[0]+"_tiles.json"
    with open(json_filename, "w") as outfile:
        json.dump(tile_dict, outfile)

    return tile_dir, json_filename


def recursive_file_save(file_name, pathname=""):
    """

    """

    x = 0
    if not os.path.exists(file_name):
        # save file
    else:
        x += 1
        file_name = file_name+f" ({x})"
        recursive_file_save(file_name)



def create_tiles(template_image, pathname):
    """
    Creates RGB dictionary, saves to json, resizes and saves as tiles.
    """

    # Creates a directory to hold tiles if it does not exist
    tile_dir = pathname+"_tiles"
    if not os.path.exists(tile_dir):
        os.mkdir(tile_dir)

    # Creates RGB dictionary from tiles, saves to json file
    # Resizes and save tiles to new directory
    tile_dir, json_filename = create_dict_resize_save_tiles(size, pathname)

    return tile_dir, json_filename


def get_rgb(img_object):
    """
    Generates 3 numerical values (red, green, blue)
    for each pixel in an image and returns the average value.
    """

    rgb_list = list(img_object.getdata())
    pixels = len(rgb_list)
    r, g, b = 0, 0, 0
    for pixel in rgb_list:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    average_rgb = [int(r/pixels), int(g/pixels), int(b/pixels)]
    return average_rgb

def crop_mosaic_get_rgb(size, column, row, image):
    """
    Crops a tile out of the mosaic and extracts the RGB value.
    """

    # Crop coordinatees
    top = int(size * column)# x
    left = int(size * row) # y
    bottom = int(size * (column + 1)) # x
    right = int(size * (row + 1)) # y
    coordinates = (left, top, right, bottom)

    # Getting RGB from cropped image tile
    im1 = image.crop(coordinates)
    portrait_rgb = get_rgb(im1)
    portrait_rgb = portrait_rgb[0]+portrait_rgb[1]+portrait_rgb[2]

    return portrait_rgb, coordinates

def find_best_match(tile_dir, tile_data, portrait_rgb, im, coordinates):
    """
    Searches tile json data for closes rgb match to mosaic tile.
    """

    best_match = ""
    best_match_diff = 10000 # Arbitrary #, will be replaced with first iteration

    for tile in tile_data:
        tile_rgb = tile_data[tile][0]+tile_data[tile][1]+tile_data[tile][2]
        if tile_rgb > portrait_rgb:
            diff = tile_rgb - portrait_rgb
        else:
            diff = portrait_rgb - tile_rgb

        if diff < best_match_diff:
            best_match_diff = diff
            best_match = tile

    paste_path = os.path.join(tile_dir, best_match)
    with Image.open(paste_path).convert("RGB") as paste_image:
        im.paste(paste_image, coordinates)


def compose_mosaic(tile_dir, json_filename, template_file, image_name):
    """
    Breaks portrait into small square tiles.
    Uses json file to find best suited match for each tile.
    Pastes the best match onto the mosaic image.
    """

    # Calculates how many rows and columns are needed
    with Image.open(template_file).convert("RGB") as im:
        size = round(im.width*tile_percentage_num)
        rows = round(im.width/size)
        columns = round(im.height/size)

        # Think of grid where origin is top left on image
        with open(json_filename) as infile:
            tile_data = json.loads(infile.read())
            print("Composing mosaic...")
            for a in range(columns):
                for b in range(rows):
                    # Obtain cropped image tile RGB
                    portrait_rgb, coordinates = crop_mosaic_get_rgb(size, a, b, im)

                    # Find the best tile match and paste to mosaic
                    find_best_match(tile_dir, tile_data, portrait_rgb, im, coordinates)

        im_dir = os.path.join(os.getcwd(), "mosaics")
        # Check for 'mosaics' directory
        if not os.path.exists(im_dir):
            os.mkdir(im_dir)
        im_path = os.path.join(im_dir, image_name+".jpg")
        if not im_path:
            im.save(im_path, "JPEG")
        with Image.open(template_file).convert("RGB") as original:
            original.show(template_file)
        im.show(im_path)


def file_cleanup(json_filename, tile_dir=""):
    """
    Removes json file and tile directory.
    """

    subprocess.run(["rm", json_filename])
    if os.path.exists(tile_dir):
        subprocess.run(["rm", "-r", tile_dir])


def verify_CLA():
    """
    Verifies the command line arguments given by user.
    """
    arguments = sys.argv[1:]
    valid_ext = ["jpg", "jpeg", "png"]
    try:
        # Argument 1 checks
        if not os.path.exists(arguments[0]):
            sys.exit(f"Could not find {arguments[0]}.")
        if os.path.getsize(arguments[0]) == 0:
            sys.exit(f"{arguments[0]} is an invalid file.")
        if arguments[0].split(".")[-1] not in valid_ext:
            print(arguments[0].split(".")[-1])
            sys.exit(f"{arguments[0]} is an invalid file type.")

        # Argument 2 checks
        if len(arguments) > 1:
            if not os.path.exists(arguments[1]):
                sys.exit(f"Could not find {arguments[1]}.")
            if len(os.listdir(arguments[1])) == 0:
                sys.exit(f"There are no files in {arguments[1]}.")
    except IndexError as e:
        sys.exit(e)


def disk_usage():
    """
    Checks size of directory/subdirectories after program runs.
    If over 1 GB, prints a message on the console.
    """

    file_size = str(subprocess.check_output(["du",  "-s"]))
    file_size = int(re.findall(r"\d+", file_size)[0])/1000/1000
    if file_size >= 1:
        print("This directory is over 1 GB.")


def logging(data=""):
    """
    Creates log.txt if none exists.
    Logs data/time, command line args, and any user input.
    """

    if not os.path.exists("log.txt"):
        subprocess.run(["touch", "log.txt"])

    date_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    subprocess.run(f"echo {date_time} >> log.txt", shell=True)

    if len(sys.argv) > 1:
        string = f"Command line arguments: '{sys.argv[1:][0]}'"
        subprocess.run(f"echo {string} >> log.txt", shell=True)

    if data:
        string = f"User input: '{data}'"
        subprocess.run(f"echo {string} >> log.txt", shell=True)

    subprocess.run("echo ------------------------------------ >> log.txt", shell=True)



def main():
    # Only 2 command line arguments are valid
    if len(sys.argv) != 3:
        sys.exit("Must have 2 command line arguments <program> <image_name> <image_directory>.")

    # verify_CLA()

    template_image = sys.argv[1]
    image_dir = sys.argv[2]
    mosaic_name = template_image.split(".")
    try:
        mosaic_name = mosaic_name[0]+"_mosaic."+mosaic_name[1]
    except IndexError:
        pass

    # Derive dimensions from portrait
    with Image.open(template_image).convert("RGB") as im:
        size = round(im.width*tile_percentage_num)
        size = (size, size)

    # Create the tiles
    tile_dir, json_filename = create_tiles(template_image, image_dir)

    # Compose the mosaic
    compose_mosaic(tile_dir, json_filename, template_image, image_name)

    # Remove files and directories
    file_cleanup(json_filename, tile_dir)

    # Disk usage, logging, and exit
    disk_usage()
    if 'user_input' in locals():
        logging(user_input)
    sys.exit()


if __name__ == "__main__":
    main()
