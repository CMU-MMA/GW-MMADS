import requests
import os
import os.path as pa
import pandas as pd
import argparse

###############################################################################

###############################################################################

##############################
###     Setup argparse     ###
##############################

# parser object
parser = argparse.ArgumentParser("Download proprietary files.")

# File with exposure info
parser.add_argument("-f", "--file_info", type=str, help="Path to file containing file info, esp. md5sums and file names.", required=True)

# Destination directory for files
parser.add_argument("-o", "--outdir", type=str, default=f"{pa.dirname(__file__)}/download_proprietary_files", help="Destination directory for files")

# Authentication token for NOIRLab Astro Data Archive
parser.add_argument("-t", "--token", type=str, help="NOIRLab ADA authentication token; see https://github.com/NOAO/nat-nb/blob/master/api-authentication.ipynb for instructions on how to generate a token.")

###############################################################################

##############################
###          Setup         ###
##############################

# Parse args
args = parser.parse_args()

# Initialize API things 
headers = dict(Authorization=args.token)
fileurl_template = f"https://astroarchive.noirlab.edu/api/retrieve/FILEID"

# Open file info file
df_files = pd.read_csv(args.file_info)

# Create outdir if it does not exist
os.makedirs(args.outdir, exist_ok=True)

##############################
###     Download files     ###
##############################

# Iterate over files 
for i, f in df_files.iterrows():
    fileurl = fileurl_template.replace("FILEID", f["md5sum"])
    r = requests.get(fileurl, headers=headers)
    if r.status_code == 200:
        print(f"Retrieved file {f['archive_filename']} with size={len(r.content):,} bytes")
        # Write to file
        open(f"{args.outdir}/{pa.basename(f['archive_filename'])}", "wb").write(r.content)
    else:
        msg = f'Error getting file ({requests.status_codes._codes[r.status_code][0]}). {r.json()["message"]}'
        print(msg)
        continue