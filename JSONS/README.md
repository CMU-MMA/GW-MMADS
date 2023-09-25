## JSON Creation 

Using the output of gwemopt (i.e., schedule_decam.dat) you can use this code as 

python gwemopt_to_json_DECam.py /Users/brendan/Documents/research/DECam/GWMMADS/JSONS/S230922g/09-23-23/schedule_decam.dat 2022B-922046 S230922g

where you need to specify the path to the file, the program ID, and the name of the GW event. 

In your current working directory it will create a folder for the name of the event and then a folder within that for the date (i.e., /JSONS/S230922g/09-23-23/). 

Be careful to select the correct proposal ID for the target type:

### BBH: 2022B-715089
### NSs: 2022B-922046
### Survey : xxx
