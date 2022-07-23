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


def create_tiles(template_image, size, image_dir):
    """
    Creates RGB dictionary, saves to json, resizes and saves as tiles.
    """

    # Creates a directory to hold tiles if it does not exist
    tile_dir = image_dir+"_tiles"
    if not os.path.exists(tile_dir):
        os.mkdir(tile_dir)

    # Creates RGB dictionary from tiles, saves to json file
    # Resizes and saves tiles to a new directory
    tile_dict = {}
    for file in os.listdir(image_dir):
        filename = os.path.join(image_dir, file)
        with Image.open(filename).convert("RGB") as im:
            im1 = im.resize(size)
            # Get image average RGB while file is open, add to dictionary
            if filename not in tile_dict:
                tile_dict[file] = get_rgb(im1)
            # Save tile to new directory
            im1.save(os.path.join(tile_dir, file), "JPEG")

    # Save tile_dict to json file
    json_filename = os.path.basename(image_dir).split(".")[0]+"_tiles.json"
    with open(json_filename, "w") as outfile:
        json.dump(tile_dict, outfile)

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

def find_best_match(tile_data, portrait_rgb):
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

    return best_match


def rename_mosaic(template_image):
    """
    Creates filename for mosaic image
    """

    if template_image.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_split = template_image.rsplit(".", 1)
        mosaic_name = image_split[0]+"_mosaic."+image_split[1]
    else:
        mosaic_name = mosaic_name[0]+"_mosaic"

    return mosaic_name


def recursive_save(file, image, pathname="", x=1):
    """
    Saves copies of files in a 'filename(#).ext' format
    """

    pathname = file.rsplit("/", 1)[0]
    if os.path.exists(file):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_split = file.rsplit(".", 1)
            ext = file_split[1]
            file = file_split[0]
        basename = file.split("(")[0]
        file = f"{basename}({x}).{ext}"
        x += 1
        recursive_save(file, image, x=x)
    else:
        image.save(file, "JPEG")

    return file


def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


def compose_mosaic(tile_dir, json_filename, template_file, mosaic_name, mosaic_dir="mosaics"):
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
                    best_match = find_best_match(tile_data, portrait_rgb)

                    # Paste best match tile onto mosaic
                    paste_path = os.path.join(tile_dir, best_match)
                    with Image.open(paste_path).convert("RGB") as paste_tile:
                        im.paste(paste_tile, coordinates)

        mosaic_file = os.path.join(mosaic_dir, mosaic_name)
        mosaic_file = recursive_save(mosaic_file, im)
        basename = mosaic_file.rsplit("/", 1)[1]
        print(f"Saved {basename}.")

    # Shows both the orginal and mosaic images
    open_file(template_file)
    open_file(mosaic_file)

    return


def file_cleanup(json_filename, tile_dir=""):
    """
    Removes json file and tile directory.
    """

    subprocess.run(["rm", json_filename])
    if os.path.exists(tile_dir):
        subprocess.run(["rm", "-r", tile_dir])


def verify_args():
    """
    Verifies the command line arguments given by user.
    """

    arguments = sys.argv[1:]
    try:
        # Verifies image and image_dir exist
        if not os.path.exists(arguments[0]):
            sys.exit(f"Could not find {arguments[0]}.")
        if not os.path.exists(arguments[1]):
            sys.exit(f"Could not find {arguments[1]}.")

        # Verify image file has a size and image dir has files
        if os.path.getsize(arguments[0]) == 0:
            sys.exit(f"{arguments[0]} is an invalid file.")
        if len(os.listdir(arguments[1])) == 0:
            sys.exit(f"There are no files in {arguments[1]}.")

        # Verify image is an image file
        if not arguments[0].lower().endswith(('.png', '.jpg', '.jpeg')):
            sys.exit(f"{arguments[0]} is an invalid file type.")

    except IndexError as e:
        sys.exit(e)


def logging(data=""):
    """
    Creates log.txt if none exists.
    Logs data/time, command line args, and any user input.
    """

    subprocess.run("echo ------------------------------------ >> log.txt", shell=True)

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


def main():
    # Logging
    logging()

    # Verify command line args
    if len(sys.argv) != 3:
        sys.exit("Must have 2 command line arguments <program> <image_name> <image_directory>.")
    verify_args()

    # Create variables from args
    template_image = sys.argv[1]
    image_dir = sys.argv[2]
    mosaic_name = rename_mosaic(template_image)

    # Derive dimensions from portrait
    with Image.open(template_image).convert("RGB") as im:
        size = round(im.width*tile_percentage_num)
        size = (size, size)

    # Create the tiles
    tile_dir, json_filename = create_tiles(template_image, size, image_dir)

    # Creates 'mosaics' dir if one does not exist
    mosaic_dir = os.path.join(os.getcwd(), "mosaics")
    if not os.path.exists(mosaic_dir):
        os.mkdir(mosaic_dir)

    # Compose the mosaicQ
    compose_mosaic(tile_dir, json_filename, template_image, mosaic_name)

    # Remove files and directories
    file_cleanup(json_filename, tile_dir)

    # Exit program
    sys.exit()


if __name__ == "__main__":
    main()
