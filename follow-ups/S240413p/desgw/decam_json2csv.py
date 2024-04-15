import glob
import json

import numpy as np
import pandas as pd

###############################################################################


def decam_json2df(json_file, csv_file):
    # Load JSON
    with open(json_file) as f:
        data = json.load(f)

    # Read ra, dec, filter from json
    ras = []
    decs = []
    filters = []
    objects = []
    for exp in data:
        ras.append(exp["RA"])
        decs.append(exp["dec"])
        filters.append(exp["filter"])
        objects.append(exp["object"])

    # Cast into dataframe
    df = pd.DataFrame({"ra": ras, "dec": decs, "fil": filters, "obj": objects})

    return df


###############################################################################

JSONDIR = "S240413p_jsons_update"

for f in glob.glob(f"{JSONDIR}/*.json"):
    csv = f.replace(".json", ".csv")
    df = decam_json2df(f, csv)
    df.to_csv(csv, index=False)
