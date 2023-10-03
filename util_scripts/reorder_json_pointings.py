import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

###############################################################################

def reorder_df(df, angle):
    # Calculate metric, based on slices parallel to angle
    df["metric"] = np.sin(angle) * df["RA"] + np.cos(angle) * df["dec"]

    # Sort by metric 
    df_sorted = df.sort_values(by="metric")

    # Calculate distances between consecutive points
    for d in [df, df_sorted]:
        d[["deltaRA", "deltadec"]] = d[["RA", "dec"]].diff(axis=0)
        d["diff"] = (d["deltaRA"]**2 + d["deltadec"]**2)**0.5

    # Make the pattern snake (switch directions at long jumps)
    long_jump = df_sorted["diff"] > 5 # (degrees)
    long_jump_indices = np.where(long_jump.values)[0] 
    # long_jump_indices = np.where((df_sorted["deltaRA"] < 0).values)[0] # This line switches every time the deltaRA is negative
    switch = False
    for lji in long_jump_indices:
        if switch:
            end_index = lji
            df_sorted.iloc[start_index:end_index] = df_sorted.iloc[start_index:end_index][::-1]
        else:
            start_index = lji
        # Flip switch
        switch = ~switch

    return df_sorted

def score_reordering(df):
    # Calculate diagnostics
    dict_diag = {} 
    dict_diag["median"] = df["diff"].median()
    dict_diag["mean"] = df["diff"].mean()
    dict_diag["std"] = df["diff"].std()

    df["diff5"] = df["diff"] - 5
    df.loc[df["diff5"] < 0, "diff"] = 0
    dict_diag["mean5"] = df["diff5"].mean()

    # Return score, with the convention that larger scores are better
    return -dict_diag["mean5"]


def optimize_reordering(df):
    # Iterate over angles
    best_score = -np.inf
    best_df = None
    best_angle = None
    for angle in np.linspace(0, 2 * np.pi, 100):
        df_sorted = reorder_df(df, angle)
        score = score_reordering(df)
        if score > best_score:
            best_df = df_sorted
            best_angle = angle

    return best_df, best_angle

###############################################################################

##############################
###     Setup argparse     ###
##############################

# parser object
parser = argparse.ArgumentParser("Order DECam json by increasing RA.")

# json_file 
parser.add_argument("-f", "--json_file", type=str, help="Path to the DECam json to reorder", required=True)

# suffix to append to files
parser.add_argument("-s", "--suffix", type=str, default="reordered", help="Suffix to add immediately before the .json extension in the new file")

# Boolean specifying to write json or not
parser.add_argument("-w", "--write_json", action="store_true", help="Boolean; if true, write reordered json")

# Only use the first n pointings 
parser.add_argument("-n", "--nmax_pointings", type=int, default=1000, help="Maximum number of pointings to use from json")

# Boolean specifying whether to make plots or not 
parser.add_argument("-p", "--plot", action="store_true", help="Show diagnostic plots")

###############################################################################

##############################
###          Setup         ###
##############################

# Parse args
args = parser.parse_args()

# Read json as dataframe
with open(args.json_file, "r") as f:
    js = json.load(f)
    js_cut = js[args.nmax_pointings:]
    js = js[:args.nmax_pointings]
    df = pd.DataFrame(js)
    df_cut = pd.DataFrame(js_cut)

##############################
###   Reorder pointings    ###
##############################

# Calculate ordering metric 
# Currently this is a cherrypicked metric for DELVE, though the idea can be applied to other tilings
# The general idea is to find a way to slice the pointings into groups parallel to one of the tiling axes;
#   at the moment this works best for DELVE when slicing ~horizontally,
#   and then reversing every other slice to snake across the area.
# Normalize RA, dec
for c in ["RA", "dec"]:
    df[f"{c}_norm"] = (df[c] - df[c].median()) / (df[c].max() - df[c].min())
# Calculate metric
# Metric for ~horizontal stripes
# -0.13 is good for S230922g full area
# 0.01 is good for S230922g 72/85 pointings
# Circular metric used for cut pointings also doesn't perform too terribly
df["metric"] = -0.13 * df["RA_norm"] + df["dec_norm"]
df["metric"] = 0.01 * df["RA_norm"] + df["dec_norm"]
# df["metric"] = np.arctan2(df["dec_norm"], df["RA_norm"]) 

# Sort df by metric 
df_sorted = df.sort_values(by="metric")

# Calculate distances between consecutive points
for d in [df, df_sorted]:
    d[["deltaRA", "deltadec"]] = d[["RA", "dec"]].diff(axis=0)
    d["diff"] = (d["deltaRA"]**2 + d["deltadec"]**2)**0.5

# Make the pattern snake (switch directions at long jumps)
long_jump = df_sorted["diff"] > 5 # (degrees)
long_jump_indices = np.where(long_jump.values)[0] 
# long_jump_indices = np.where((df_sorted["deltaRA"] < 0).values)[0] # This line switches every time the deltaRA is negative
switch = False
for lji in long_jump_indices:
    if switch:
        end_index = lji
        df_sorted.iloc[start_index:end_index] = df_sorted.iloc[start_index:end_index][::-1]
    else:
        start_index = lji
    # Flip switch
    switch = ~switch

# # Call optimization
# This theoretically should use the functions defined above to cycle through the possible slicing angles,
#   but right now it is outperformed by the cherrypicked slice angle above
# df_sorted, best_angle = optimize_reordering(df)

# Use index of df to sort json
print(df_sorted)
js_sorted = [js[i] for i in df_sorted.index]

# Simple sort for cut pointings
if args.nmax_pointings != parser.get_default("nmax_pointings"):
    for c in ["RA", "dec"]:
        df_cut[f"{c}_norm"] = (df_cut[c] - df_cut[c].median()) / (df_cut[c].max() - df_cut[c].min())
    # Metric for ~RA ordering
    df_cut["metric"] = -10 * df_cut["RA_norm"] + df_cut["dec_norm"] 
    # Metric for covering pointings in a circle path
    df_cut["metric"] = np.arctan2(df_cut["dec_norm"], df_cut["RA_norm"]) 
    df_cut_sorted = df_cut.sort_values(by="metric")
    js_cut_sorted = [js_cut[i] for i in df_cut_sorted.index]

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

# Plot, if specified
if args.plot:
    mosaic = [["df", "df_sorted"], ["df_hist", "df_sorted_hist"]]
    fig, axd = plt.subplot_mosaic(mosaic, figsize=(8,8))
    for a, d in zip(["df", "df_sorted"], [df, df_sorted]): 
        # Scatter plot
        ax = axd[a]
        ax.plot(d["RA"], d["dec"], marker="o")
        if args.nmax_pointings != parser.get_default("nmax_pointings"):
            ax.plot(df_cut_sorted["RA"], df_cut_sorted["dec"], color="r", marker="o")
        ax.invert_xaxis()
        ax.grid()
        ax.set(
            aspect="equal",
            xlabel="RA (deg)",
            ylabel="dec (deg)",
            title={
                "df": "gwemopt",
                "df_sorted": "reordered"
            }[a],
        )

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
outname = args.json_file
if args.nmax_pointings != parser.get_default("nmax_pointings"):
    outname = outname.replace(".json", f".n{args.nmax_pointings}.json")
outname = outname.replace(".json", f".{args.suffix}.json")
outname_cut = outname.replace(".json", ".cut.json")

# Write
if args.write_json:
    with open(outname, "w") as f:
        json.dump(js_sorted, f, indent=4)
    with open(outname_cut, "w") as f:
        json.dump(js_cut_sorted, f, indent=4)
else:
    print("write_json is false; reordered json not written.")