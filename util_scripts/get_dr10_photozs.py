import numpy as np
import pandas as pd
import argparse
from astropy.io import fits

###############################################################################

def floor_base(x, base=5):
    return base * np.floor(x/base)

def dec2pm0dec(dec):
    if dec >= 0:
        return f"p{dec:03d}"
    else:
        return f"m{-dec:03d}"

def brickname2sweeprange(brickname):
    # Break apart brickname
    ra = float(brickname[:3])
    if brickname[4] == "p":
        dec = float(brickname[5:-1])
    elif brickname[4] == "m":
        dec = -float(brickname[5:-1])

    # Generate sweeprange 
    ra0 = floor_base(ra)
    dec0 = floor_base(dec)
    ra1 = floor_base(ra + 5)
    dec1 = floor_base(dec + 5)
    sweeprange = f"{int(ra0):03d}{dec2pm0dec(int(dec0))}-{int(ra1):03d}{dec2pm0dec(int(dec1))}"

    return sweeprange 

###############################################################################

##############################
###     Setup argparse     ###
##############################

# parser object
parser = argparse.ArgumentParser("Manually get DR10 photozs on NERSC")

# Path/to/*.csv; the only required column is one containing the LS UID (<brickname>_<objid>)
parser.add_argument("-f", "--csv_file", type=str, help="Path to the csv with LS UIDs (<brickname>_<objid>)", required=True)

# Column name of the UID column 
parser.add_argument("-c", "--uid_column", type=str, help="Name of the UID column", required=True)

# Path/to/survey-brick.fits.gz (LS summary file)
parser.add_argument("-s", "--survey_bricks_path", type=str, help="Path to the LS survey-bricks.fits.gz file", default="/global/cfs/cdirs/cosmo/data/legacysurvey/dr10/survey-bricks.fits.gz",)

# Path/to/photoz_dir
parser.add_argument("-d", "--photoz_dir", type=str, help="Path to the photoz directory", default="/global/cfs/cdirs/desicollab/users/rongpu/data/ls_dr10.1_photoz",)

# Use pz_with_i 
parser.add_argument("-i", "--with_i", action="store_true", help="Flag to use pz_with_i instead of pz")

###############################################################################

##############################
###          Setup         ###
##############################

# Parse args
args = parser.parse_args()

# Load csv
df_csv = pd.read_csv(args.csv_file)

# Verify that UID column exists
assert args.uid_column in df_csv.columns

# Add ls_brickname and ls_objid columns to df_csv
df_csv[["ls_brickname", "ls_objid"]] = df_csv[args.uid_column].apply(lambda x: pd.Series(x.split("_")))
df_csv["ls_objid"] = pd.to_numeric(df_csv["ls_objid"])

# Convert bricknames to sweep ranges
df_csv["ls_sweeprange"] = df_csv["ls_brickname"].apply(brickname2sweeprange)

### Get brickids
with fits.open(args.survey_bricks_path) as hdul:
    data = hdul[1].data
    df_csv["ls_brickid"] = df_csv["ls_brickname"].apply(lambda x: data[data["BRICKNAME"] == x][0]["BRICKID"])

# Complete path to photoz sweeps
PZSWEEPDIR = f"{args.photoz_dir}/pz/south"
if args.with_i:
    PZSWEEPDIR = PZSWEEPDIR.replace("/pz/", "/pz_with_i/")

print(df_csv)

##############################
###      Get photozs       ###
##############################

def radec2brickname(ra,dec):
    if dec >= 0:
        return f"{int(ra):03d}p{int(dec):03d}"
    else:
        return f"{int(ra):03d}m{-int(dec):03d}"

def get_photoz(row):
    with fits.open(f"{PZSWEEPDIR}/sweep-{row['ls_sweeprange']}-pz.fits") as hdul:
        data = hdul[1].data
        # Try returning one row
        try:
            match = data[(data["BRICKID"] == row["ls_brickid"]) & (data["OBJID"] == row["ls_objid"])]
            # The commented out lines were used to check if the object had photozs in other bricks, but it does not look like this is the case
            # if match["Z_PHOT_MEAN"] == -99.0:
            #     raise IndexError
            return match[0] 
        # If no rows matched, search nearby bricks
        except IndexError:
            # Extract decimal ra/dec from brickname
            # Note that we don't divide by 10, so these are in units of tenths of a degree
            brickra = float(row["ls_brickname"][:4])
            brickpmdec = row["ls_brickname"][4:]
            if brickpmdec[0] == "p":
                brickdec = float(brickpmdec[1:])
            elif brickpmdec[0] == "m":
                brickdec = -float(brickpmdec[1:])

            # Generate ra/decs for neighboring bricks
            neighbor_radecs = [
                (brickra - 50, brickdec - 50),
                (brickra - 50, brickdec),
                (brickra - 50, brickdec + 50),
                (brickra, brickdec - 50),
                (brickra, brickdec + 50),
                (brickra + 50, brickdec - 50),
                (brickra + 50, brickdec),
                (brickra + 50, brickdec + 50),
            ]

            # Convert to sweepranges
            neighbor_sweepranges = [radec2brickname(*x) for x in neighbor_radecs]            

            # Iterate over neighboring sweepranges
            for sr in neighbor_sweepranges:
                with fits.open(f"{PZSWEEPDIR}/sweep-{brickname2sweeprange(sr)}-pz.fits") as hdul:
                    data = hdul[1].data
                    # Try returning one row
                    try:
                        match = data[(data["BRICKID"] == row["ls_brickid"]) & (data["OBJID"] == row["ls_objid"])]
                        return match[0] 
                    except IndexError:
                        continue

            # Return row of nans if no match found
            return [np.nan] * 14 
        except:
            raise
        

# Get result
result = df_csv.apply(get_photoz, axis=1)

# Append result to df_csv
result = pd.DataFrame([list(r) for r in result], columns=[f"ls_{x}" for x in result[0].array.names])
result.drop(labels=["ls_BRICKID", "ls_OBJID"], axis=1, inplace=True)
df_plus = pd.concat([df_csv, result], axis=1)

# Save
if args.with_i:
    df_plus.to_csv(args.csv_file.replace(".csv", ".photoz_with_i.csv"))
else:
    df_plus.to_csv(args.csv_file.replace(".csv", ".photoz.csv"))
