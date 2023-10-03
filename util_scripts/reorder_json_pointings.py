import numpy as np
import pandas as pd
import json
import argparse
import matplotlib.pyplot as plt

###############################################################################

##############################
###     Setup argparse     ###
##############################

# parser object
parser = argparse.ArgumentParser("Order DECam json by increasing RA.")

# path_to_json
parser.add_argument("-p", "--path_to_json", type=str, help="Path to the DECam json to reorder", required=True)

# suffix to append to files
parser.add_argument("-s", "--suffix", type=str, default="reordered", help="Suffix to add immediately before the .json extension in the new file")

# Boolean specifying to write json or not
parser.add_argument("-w", "--write_json", action="store_true", help="Boolean; if true, write reordered json.")

###############################################################################

##############################
###          Setup         ###
##############################

# Parse args
args = parser.parse_args()

# Read json as dataframe
with open(args.path_to_json, "r") as f:
    js = json.load(f)
    df = pd.DataFrame(js)

##############################
###   Reorder pointings    ###
##############################

# Calculate weighted metric
# This metric applies a strong weighting on RA, and a smaller one on dec,
#   s.t. ea. RA "stripe" should be taken in one block 
# Rotate RA, dec to align with grid
# Normalize RA, dec
for c in ["RA", "dec"]:
    df[f"{c}_norm"] = (df[c] - df[c].min()) / (df[c].max() - df[c].min())
# Calculate metric
# Metric for ~horizontal stripes
df["metric"] = -0.13 * df["RA_norm"] + df["dec_norm"]
## Metric for +slope stripes
#df["metric"] = 1.4 * df["RA_norm"] + df["dec_norm"]
## Metric for -slope stripes (not very well tuned)
#df["metric"] = 1.32 * df["RA_norm"] - df["dec_norm"]

# Sort df by metric 
df_sorted = df.sort_values(by="metric")

# Calculate distances between consecutive points
for d in [df, df_sorted]:
    d[["deltaRA", "deltadec"]] = d[["RA", "dec"]].diff(axis=0)
    d["diff"] = (d["deltaRA"]**2 + d["deltadec"]**2)**0.5

# Make the pattern snake (switch directions at long jumps)
long_jump = df_sorted["diff"] > 5 # (degrees)
long_jump_indices = np.where(long_jump.values)[0] 
switch = False
for lji in long_jump_indices:
    print(lji)
    if switch:
        end_index = lji
        df_sorted.iloc[start_index:end_index] = df_sorted.iloc[start_index:end_index][::-1]
    else:
        start_index = lji
    # Flip switch
    switch = ~switch

# Use index of df to sort json
print(df_sorted)
js_sorted = [js[i] for i in df_sorted.index]

##############################
###   Print diagnostics    ###
##############################

# Calculate distances between consecutive points
for d in [df, df_sorted]:
    d[["deltaRA", "deltadec"]] = d[["RA", "dec"]].diff(axis=0)
    d["diff"] = (d["deltaRA"]**2 + d["deltadec"]**2)**0.5

# Print diagnostics
print("#" * 10, "DIAGNOSTICS", "#" * 10)
df_diag = pd.DataFrame(index=["median", "mean", "std"], columns=["gwemopt", "sorted"])
for c, d in zip(df_diag.columns, [df, df_sorted]):
    df_diag.loc["median", c] = d["diff"].median()
    df_diag.loc["mean", c] = d["diff"].mean()
    df_diag.loc["std", c] = d["diff"].std()
print(df_diag)
print("#" * 33)

mosaic = [["df", "df_sorted"], ["df_hist", "df_sorted_hist"]]
fig, axd = plt.subplot_mosaic(mosaic, figsize=(8,8))
for a, d in zip(["df", "df_sorted"], [df, df_sorted]): 
    # Scatter plot
    ax = axd[a]
    ax.plot(d["RA"], d["dec"], marker="o")
    ax.invert_xaxis()
    ax.set_aspect("equal")
    ax.set_xlabel("RA (deg)")
    ax.set_ylabel("dec (deg)")
    ax.set_title({
        "df": "gwemopt",
        "df_sorted": "reordered"
    }[a])
    ax.grid()

    # Histogram of slew distances
    ax = axd[f"{a}_hist"]
    ax.hist(d["diff"], bins=np.linspace(0,25,50))
    ax.set_xlabel(r"$\Delta \theta$ (deg)")
    ax.set_ylabel(r"$N$")
plt.tight_layout()
plt.show()
plt.close()

##############################
###     Write to file      ###
##############################

# Make filename
outname = args.path_to_json.replace(".json", f".{args.suffix}.json")

# Write
if args.write_json:
    with open(outname, "w") as f:
        json.dump(js_sorted, f, indent=4)
else:
    print("write_json is false; reordered json not written.")