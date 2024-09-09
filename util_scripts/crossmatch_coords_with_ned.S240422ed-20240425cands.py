import numpy as np
from astropy.coordinates import SkyCoord, Angle
from astropy.io import fits
import astropy.units as u
from astropy.table import Table, vstack

PATH_TO_NED = "/home/tomas/academia/projects/decam_followup_O4/crossmatch/ned/NEDLVS_20210922_v2.fits"

ned = Table.read(PATH_TO_NED)

nedscs = SkyCoord(ned["ra"], ned["dec"], unit=(u.deg, u.deg))
print(nedscs)

objnames = [
    "C202404240825050m202623",
    "T202404230819066m224522",
    "T202404240824462m330712",
    "T202404230814209m314347",
    "T202404240826256m240205",
    "T202404240828350m244053",
    "T202404240758367m263506",
    "T202404240802269m260722",
    "T202404240823455m231322",
    "T202404250838088m123324",
    "T202404250836082m185429",
    "C202404240828218m203133",
    "T202404240834020m183108",
    "T202404240830378m244246",
    "T202404240826294m232502",
    "C202404240827527m244646",
    "T202404230814209m314347",
    "T202404230815334m263446",
    "T202404240819363m260708",
    "T202404230810551m184810",
]

ned_matches = []
ned_match_inds = []
ned_seps = []
for objname in objnames:
    print(objname)
    # Get ra, dec
    ra_str = objname[9:16]
    ra = Angle(float(ra_str[:2]) + float(ra_str[2:4])/60 + float(ra_str[4:])/3600/10, unit=u.hourangle)
    dec_str = objname[16:]
    dec = Angle(float(dec_str[1:3]) + float(dec_str[3:5])/60 + float(dec_str[5:])/3600, unit=u.deg)
    if dec_str[0] == "m":
        dec *= -1

    # Crossmatch with ned
    objscs = SkyCoord(ra, dec)
    xm = objscs.separation(nedscs)
    match_ind = np.argmin(xm)
    match_ned = ned[match_ind]
    ned_matches.append(ned_matches)
    ned_match_inds.append(match_ind)
    ned_seps.append(xm[match_ind])

# ned_matches = vstack(ned_matches)
ned_matches = ned[ned_match_inds]
ned_matches["sep"] = ned_seps

# zero out things too far away from pseudohost
mask = (ned_matches["sep"] * np.pi / 180) < (50 / 188000) # search radius of 50 kpc / S240422ed distance of 188 Mpc
ned_matches[~mask] = 0

# Add objids
ned_matches["objid"] = objnames
ned_matches.write("/home/tomas/academia/projects/decam_followup_O4/S240422ed/240423_shortlist_ned_crossmatch.S240422ed-20240425cands.csv", format="csv", overwrite=True)
print(ned_matches)

