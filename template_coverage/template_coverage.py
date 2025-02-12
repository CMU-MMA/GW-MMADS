import os
import os.path as pa
import requests
import subprocess
import pandas as pd

###############################################################################

NATROOT = "https://astroarchive.noirlab.edu"
ADSURL = f"{NATROOT}/api/adv_search"

JJ = {
    "outfields": [
        "ra_center",
        "dec_center",
        "ifilter",
        "EXPNUM",
        "exposure",
        "proposal",
        "OBJECT",
    ],
    "search": [
        ["instrument", "decam"],
        ["obs_type", "object"],
        ["proc_type", "instcal"],
        ["prod_type", "image"],
    ],
}

###############################################################################

propids = {
    "DES": "2012B-0001",
    "DECaLS": ["2014B-0404", "2016A-0190"],
    "DELVE": "2019A-0305",
    "DECaPS": [
        "2014A-0429",
        "2016A-0327",
        "2016B-0279",
        "2018A-0251",
        "2018B-0271",
        "2019A-0265",
    ],
    # SMASH paper: https://datalab.noirlab.edu/smash/smash_overview.pdf
}

##############################
###     Fetch/load df      ###
##############################

# Get archive images
PROJ_PATH = "/hildafs/project/phy220048p/tcabrera/decam_followup_O4/DECam_coverage"
ARCHIVE_IMAGES_PATH = f"{pa.dirname(__file__)}/template_coverage.csv"
# Fetch
apiurl = f"{ADSURL}/find/?limit=4000000"
df = pd.DataFrame(requests.post(apiurl, json=JJ).json()[1:])

# Reduce by filter
df["ifilter"] = df["ifilter"].apply(lambda x: "NaN" if x == None else x[0])
df = df[df["ifilter"].apply(lambda x: x in list("ugrizY"))]

# Apply exptime cut
df.drop(
    index=df.index[(df["ifilter"] == "g") & (df["exposure"] < 30)], inplace=True
)
df.drop(
    index=df.index[(df["ifilter"] != "g") & (df["exposure"] < 50)], inplace=True
)

# Drop duplicates
df.drop_duplicates("EXPNUM", inplace=True)

# Save
df.set_index("EXPNUM").to_csv(ARCHIVE_IMAGES_PATH)

##############################
###  Generate coverage df  ###
##############################

# Initialize df_coverage with unique ra/dec of full df
df.drop_duplicates(["ra_center", "dec_center"]).set_index(["ra_center", "dec_center"], inplace=True)
df_coverage = df.copy()
# Get filter truth columns
for f in list("ugrizY"):
    df_coverage[f] = df_coverage.index.isin(df.index[df["ifilter"] == f])
df_coverage.drop(columns=["ifilter"], inplace=True)
# Get proposal (propid) truth columns
for p in ["2012B-0001", "2014B-0404", "2019A-0305"]:
    df_coverage[p] = df_coverage.index.isin(df.index[df["proposal"] == p])
# Save
df_coverage.to_csv(f"{pa.dirname(__file__)}/template_byfilter.csv")
