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
    "T202404230842302m153558",
    "T202404230837507m163211",
    "T202404230829126m213023",
    "T202404230826379m205002",
    "T202404230821534m300608",
    "T202404220803280m260044",
    "T202404220803131m241958",
    "T202404220802104m271528",
    "T202404220743147m254551",
    "T202404230815532m163418",
    "T202404220745546m244543",
    "T202404230836407m183019",
    "T202404220754081m230446",
    "T202404230836339m160815",
    "T202404230801416m292704",
    "T202404230833162m174036",
    "T202404230830590m113510",
    "T202404230814239m162560",
    "T202404230826561m174440",
    "T202404230809061m294629",
    "T202404230814066m294350",
    "T202404230819242m155108",
    "T202404230819036m172901",
    "T202404230840463m123945",
    "A202404230835046m181621",
    "T202404230822324m184027",
    "C202404220748432m263931",
    "T202404230829340m194920",
    "T202404230832302m160508",
    "T202404230827131m201259",
    "T202404230836123m164432",
    "T202404230834494m200328",
    "T202404230834069m194223",
    "T202404230833368m182525",
    "T202404230829513m175753",
    "T202404230829280m213156",
    "T202404230828592m170245",
    "T202404230827397m144855",
    "T202404230826275m145258",
    "T202404230826239m163356",
    "T202404230823460m153056",
    "T202404230819451m135024",
    "T202404220748441m261010",
    "C202404230843427m145643",
    "C202404230840165m164738",
    "C202404230837426m143422",
    "C202404230832290m141059",
    "C202404230821039m134914",
    "C202404220807308m244513",
    "C202404230805058m235101",
    "C202404230813585m153326",
    "T202404220750120m261013",
    "T202404220802104m271528",
    "T202404220803131m241958",
    "T202404230825523m204844",
    "T202404230804442m233923",
    "C202404240825089m244346",
    "T202404230804595m312031",
    "T202404230808354m284335",
    "T202404230809168m293932",
    "T202404230816087m164211",
    "T202404230818179m150414",
    "T202404230829558m131000",
    "T202404230801416m292704",
    "T202404230809061m294629",
    "T202404230814239m162560",
    "T202404230822582m190136",
    "T202404230841039m183535",
    "T202404240825022m215047",
    "T202404230823460m153056",
    "C202404230831269m202520",
    "C202404240825596m241655",
    "T202404230815504m284010",
    "T202404220800312m260104",
    "C202404230837131m182810",
    "C202404230837079m165910",
    "T202404230828385m202260",
    "C202404230835315m170241",
    "C202404230835217m151831",
    "C202404230833144m154329",
    "C202404230831000m152059",
    "C202404230827573m170419",
    "T202404230838390m185605",
    "C202404230819576m141805",
    "C202404230815134m143338",
    "C202404230839545m171448",
    "T202404230830136m183056",
    "T202404240822491m294127",
    "T202404240823282m270944",
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
ned_matches.write("/home/tomas/academia/projects/decam_followup_O4/S240422ed/240423_shortlist_ned_crossmatch.csv", format="csv", overwrite=True)
print(ned_matches)

