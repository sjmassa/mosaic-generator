# Mosaic Generator
## Overview
Creates a mosaic of one image from a collection of images.<br />
This is stand-alone mosaic generator code from my capstone project.<br />
https://github.com/sjmassa/capstone<br /><br />
## How to run
$ <program_name> <image_name> <image_directory><br />
This script takes 2 command line arguments.<br />
Arg 1 is the image that will be made into a mosaic.<br />
Arg 2 is the directory of images that will comprise the mosaic.



## Work to do:
- **\*done\*** Rework program to run independently.
- **\*done\*** Add recursive save.
- **\*done\*** Logging: Add file/directory sizes, log errors/sys.exit()
- **\*done\*** Rework how colors of tiles and mosaics are compared.
- **\*done\*** Reduce pixel iterations when average RGB is calculated.
- Add disk/cpu/memory usage statistic/logging.
- **\*done\***Add ability to increase/decrease mosaic image size.
- **\*Abandoned/Unnecessary\*** Reduce RGB value from 256 possible to 10 in order to simplify color comarison.
- Subdivide tiles into smaller squares in order to refine color comparison.
