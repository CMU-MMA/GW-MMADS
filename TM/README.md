## TNS Reporting

We retrieved the pointings from the NOIRLAB Astro Data Archive (https://astroarchive.noirlab.edu/portal/search/) using the proposal ID, Date, and procType = raw as instcal had duplicates. The required columns in the downloaded .csv file from the archive are:

date_obs, ra, dec, ifilter, depth

For depth you must add a median value. Likely best to modify script to create median depth array using np.ones etc...
