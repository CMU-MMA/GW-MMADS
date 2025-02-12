# Template coverage

This directory contains files that can be used to identify pointings with existing data for use as templates.
The files contained are as follows:

- `template_coverage.py`: Script for querying the NOIRLab AstroDataArchive for files.
The package requirements are minimal, and should be easily installed; note that running the script will overwrite the two `.csv` files.
Presently we keep any exposures with exptimes greater than 30 (50) seconds in *g* (non-*g*) band(s).
We drop duplicate `EXPNUM`s, which should robustly keep one line per exposure; a caveat is that in a small minority of cases the ADA has multiple pointings for a single `EXPNUM`.
It is not known why this is the case; the different pointings are usually nearby one another, but are off by far larger distances than would be expected from telescope pointing errors.

- `template_coverage.csv`: `.csv` file containing the queried results from NOIRLab.
No modifications to the data structure have been applied other than cutting `ifilter` entries to the first character.

- `template_byfilter.csv`: The same information, but with the `ifilter` column replaced by a set of boolean columns (one for each filter).
This format makes it much easier to highlight coverage in certain bands in `topcat`.
Similarly, while the `proposal` column is maintained, there are also three boolean columns designating whether the pointing appears in DES, DECaLS, or DELVE.
