import numpy as np
from astropy.coordinates import SkyCoord, Angle
from astropy.cosmology import Planck15 as cosmo
from astropy.io import fits
import astropy.units as u
from astropy.table import Table, vstack

PATH_TO_NED = "/home/tomas/academia/projects/decam_followup_O4/crossmatch/ned/NEDLVS_20210922_v2.fits"

ned = Table.read(PATH_TO_NED)

nedscs = SkyCoord(ned["ra"], ned["dec"], unit=(u.deg, u.deg))
print(nedscs)

objnames = [
    "T202404220754081m230446",
    "T202404230801416m292704",
    "T202404220750120m261013",
    "T202404230827131m201259",
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
    print(ra,dec)

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
# search radius of 50 kpc / S240422ed distance of 188 Mpc ~ 0.05 z
arcsec_per_kpc = cosmo.arcsec_per_kpc_proper(0.05)
mask = ned_matches["sep"] < (50 * u.kpc * arcsec_per_kpc) 
ned_matches[~mask] = 0

# Add objids
ned_matches["objid"] = objnames
ned_matches.write("/home/tomas/academia/projects/decam_followup_O4/S240422ed/240423_shortlist_ned_crossmatch.240501.csv", format="csv", overwrite=True)
print(ned_matches)

