import glob2
import shutil
import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os.path as pa

###############################################################################

###############################################################################

##############################
###     Setup argparse     ###
##############################

# parser object
parser = argparse.ArgumentParser("Copy manually downloaded files to download.")

# Path to manually downloaded files
# This should be a path that ends like .../YYYY-MM-DD, and contains all the files that could match those downloaded
parser.add_argument("-i", "--indir", type=str, help="Path to directory of downloaded files", required=True)

# Path to directory to populate with downloaded files
# This should end like .../misc/download/<PROGRAM>/[SCIENCE,TEMPLATE]/YYYY-MM-DD; there will be several levels for HEALPix, filter, and the like below this,
#   but this script has been hard-coded to deal with it.  A future upgrade could make it a bit more flexible.
parser.add_argument("-o", "--outdir", type=str, help="Path to directory to replace with manually downloaded files", required=True)

# Boolean specifying whether to overwrite files or not
parser.add_argument("-w", "--write_files", action="store_true", help="Boolean; if true, write files. Default is False, which does a dry run of the copy.")

###############################################################################

##############################
###          Setup         ###
##############################

# Parse args
args = parser.parse_args()

##############################
###       Copy files       ###
##############################

# Get list of manually downloaded files
infiles = glob2.glob(f"{args.indir}/*")

# Get list of existing/corrupted files (for proprietary files, these will exist, but have size zero)
outfiles = glob2.glob(f"{args.outdir}/*/DECam-*/*")

# Iterate through outfiles, searching for a matching infile
for of in outfiles:
    # Get basename without file extension
    of_substr = pa.splitext(pa.basename(of))[0]
    # Drop md5sum
    of_substr = "_".join(of_substr.split("_")[1:])
    # Iterate through infiles
    if_matches = []
    for inf in infiles:
        if of_substr in pa.basename(inf):
            if_matches.append(inf)
    # Print matches
    if if_matches:
        print(f"MATCH: {if_matches} -> {of}")
    else:
        print(f"NO MATCH FOR {of}")
        continue
    # Stop if multiple matches found
    if len(if_matches) > 1:
        print(f"WARNING: MULTIPLE MATCHES FOUND; REFUSING TO COPY FILES OVER")
        continue
    # Write matches
    if args.write_files:
        shutil.copyfile(if_matches[0], of)

if not args.write_files:
    print("\nFILES NOT COPIED; ADD '-w/--write_files' FLAG TO PERFORM COPY")