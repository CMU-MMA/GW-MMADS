import pandas as pd
from astropy.time import Time
import os
import shutil
import matplotlib.pyplot as plt

directory = "/Users/brendan/Documents/research/DECam/TNS/GWMMADS/"

sourcesfile = '/Users/brendan/Documents/research/DECam/TNS/GWMMADS/SourceASSOC.csv'

usecols = ['OBJID','MJD_SCI', 'FILT_SCI', 'CMAG_APER', 'MAGERR_APER', 'RA_OBJ', 'DEC_OBJ']




     

# Pass in a Dataframe with columns Transient and Remarks
# IMPORTANT: The name we use (Transient) must be the first name it is given (from the first semester of data)
def create_bulk_info(names_types_remarks):

    print("hi")

    sources_all = pd.read_csv(sourcesfile)
    
    # Want to create a new DataFrame with columns 
    # Transient - Ra - Dec - FirstDetJD - FirstDetMag - FirstDetMagErr - FirstDetFilt - NonDetJD - NonDetLM - NonDetFilt - AT_Type - Remarks
    transients = []
    ras = []
    decs = []
    first_jds = []
    first_mags = []
    first_magerrs = []
    first_filts = []
    #nondet_jds = []
    #nondet_lms = []
    #nondet_filts = []
    at_types = []
    remarks = []
    
    for index, row in names_types_remarks.iterrows():
        transient = row['Transient'].strip() # Strip just in case
        remark = row['Remarks']
        at_type = row['AT_Type']
        
        # Make sure remark is "" not NaN
        if pd.isna(remark):
            remark = ""
            
        if pd.isna(at_type):
            at_type = "PSN"
        
        # With this we have ra, dec, and the individual name of each semester this transient comes from
        crossmatch_info = sources_all[sources_all['OBJID']==transient]
        crossmatch_info = crossmatch_info[:1]


        ra = crossmatch_info['RA_OBJ'].iloc[0]
        dec = crossmatch_info['DEC_OBJ'].iloc[0]
        first_mjd = crossmatch_info['MJD_SCI'].iloc[0]
        first_mag = crossmatch_info['CMAG_APER'].iloc[0]
        first_magerr = crossmatch_info['MAGERR_APER'].iloc[0]
        first_filt = crossmatch_info['FILT_SCI'].iloc[0]

        first_jd = Time(first_mjd, format='mjd').jd


        transients.append(transient)
        ras.append(ra)
        decs.append(dec)
        first_jds.append(first_jd)
        first_mags.append(first_mag)
        first_magerrs.append(first_magerr)
        first_filts.append(first_filt)
        #nondet_jds.append(nondet_jd)
        #nondet_lms.append(nondet_lm)
        #nondet_filts.append(nondet_filt)
        at_types.append(at_type)
        remarks.append(remark)

    data = {
        'Transient': transients,
        'Ra': ras,
        'Dec': decs,
        'FirstDetJD': first_jds,
        'FirstDetMag': first_mags,
        'FirstDetMagErr': first_magerrs,
        'FirstDetFilt': first_filts,
        'AT_Type': at_types,
        'Remarks': remarks,
    }

    print(data)

    #    'NonDetJD': nondet_jds,
    #    'NonDetLM': nondet_lms,
    #    'NonDetFilt': nondet_filts,
    
    # Put all the data together and send it over :)
    return(pd.DataFrame(data))
