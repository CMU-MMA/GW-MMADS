import json,time,sys,os,requests
from collections import OrderedDict
from datetime import datetime, timezone
import pandas as pd

# api keys in order of creation
#api_key='8db53e5dfcbebe521b6f46f13ec98b1bc37685b8'
#api_key='158a727917dae8b1e44a74ea2431c304daf568ce'
api_key='566f3108f69af96986fa8d84b073955976c41577'  # Works on real and sandbox now
bot_name='GW-MMADS_bot'
bot_id=155622

# how many second to sleep
SLEEP_SEC=1
# max number of time to check response
LOOP_COUNTER=60
# keeping sys.stdout
old_stdout=sys.stdout


# INFO FOR SANDBOX
#TNS="sandbox.wis-tns.org" # use sandbox to test first before you commit to tns website!
#url_tns_api="https://"+TNS+"/api"

# INFO FOR REAL
TNS="www.wis-tns.org" # real api url
url_tns_api="https://"+TNS+"/api"


#                0      1     2     3     4     5
# "at_types":["Other","PSN","PNV","AGN","NUC","FRB"]
at_types = {
    "Other": "0",
    "PSN": "1",
    "PNV": "2",
    "AGN": "3",
    "NUC": "4",
    "FRB": "5",
}

def get_now_str():
    now = datetime.now(timezone.utc)
    now_year = str(now.year)
    now_month = str(now.month)
    now_day = str(now.day)
    now_hour = str(now.hour)
    now_min = str(now.minute)

    if len(now_month) == 1:
        now_month = '0'+now_month
    if len(now_day) == 1:
        now_day = '0'+now_day 
    if len(now_hour) == 1:
        now_hour = '0'+now_hour
    if len(now_min) == 1:
        now_min = '0'+now_min 

    return f'{now_year}{now_month}{now_day}{now_hour}{now_min}'
    
def set_bot_tns_marker():
    tns_marker = 'tns_marker{"tns_id": "' + str(bot_id) + '", "type": "bot", "name": "' + bot_name + '"}'
    print(f"TNS: {TNS}\napi_key: {api_key}\nurl_tns_api: {url_tns_api}")
    return tns_marker

def is_string_json(string):
    try:
        json_object = json.loads(string)
    except Exception:
        return False
    return json_object

def print_status_code(response):
    json_string = is_string_json(response.text)
    if json_string != False:
        print ("status code ---> [ " + str(json_string['id_code']) + " - '" + str(json_string['id_message']) + "' ]\n")
    else:
        status_code = response.status_code
        if status_code == 200:
            status_msg = 'OK'
        elif status_code in ext_http_errors:
            status_msg = err_msg[ext_http_errors.index(status_code)]
        else:
            status_msg = 'Undocumented error'
        print ("status code ---> [ " + str(status_code) + " - '" + status_msg + "' ]\n")

def tns_search(ra,dec,radius=3):
    json_list=[("ra",f"{ra}"), ("dec",f"{dec}"), ("radius",f"{radius}"), ("units","arcsec"), 
            ("objname",""), ("objname_exact_match",0), ("internal_name",""), 
            ("internal_name_exact_match",0), ("objid",""), ("public_timestamp","")]
    search_url=f"{url_tns_api}/get/search"
    
    
    # change json_list to json format
    json_file=OrderedDict(json_list)
    # get tns_marker and create headers
    tns_marker = set_bot_tns_marker()
    headers = {'User-Agent': tns_marker}
    # construct a dictionary of api key data and search obj data
    search_data={'api_key':api_key, 'data':json.dumps(json_file)}
    print(f"search_data: \n{search_data}")
    # search obj using request module
    response=requests.post(search_url, headers=headers, data=search_data)
    # return response
    print_status_code(response)
        
    return response
    
# Calls above method and just checks if it returned anything
def tns_exist(ra,dec, radius=3): #"https://sandbox.wis-tns.org/api/get"
    '''
    Given ra and dec, and radius in arcsec, return True if already exists on TNS, otherwise return false
    '''
    response = tns_search(ra, dec, radius=radius)
    
    print(f"Response from search: ")
    print(response.content)

    if len(json.loads(response.content.decode("utf-8"))['data']['reply'])>0:
        return True
    return False


def tns_snname(ra,dec, radius=3): #"https://sandbox.wis-tns.org/api/get"
    '''
    Given ra and dec, and radius in arcsec, return snname at given position if any
    '''
    url=f"{url_tns_api}/get"
    response = tns_search(ra, dec, radius=radius, url=url, api_key=api_key)
    names = [ii['objname'] for ii in json.loads(response.content)['data']['reply']]
    if len(names)==1:
        names = names[0]
    return names

# jd = obsdate
# f = filter [g,r,i,z]
# lm = limiting flux
def non_detection(nodet_jd, nodet_f, nodet_lm):
    '''
    Create non-detection for json report
    '''
    filt_code = {'g':"21", 'r': "22", 'i':"23", 'z':"24"}
    if nodet_f not in filt_code: # If the filter given is not a real filter, assume no non-detection
        return ""
    non_detection= {
        "obsdate": "",
        "limiting_flux": "",
        "flux_units": "", #AB mag
        "filter_value": "",
        "instrument_value": "", # ctio 4m decam
        "exptime": "",
        "observer": "",
        "comments": "",
        "archiveid": "",
        "archival_remarks": "",
    }
    return non_detection

def create_photometry_group(jd, mag, magerr, filt):
    '''
    Create photometry group for json report
    '''
    photometry_group = {}
    ii = 0

    filt_code = {'g':"21", 'r': "22", 'i':"23", 'z':"24"}
    for dd, mm, merr, ff in zip(jd, mag, magerr, filt):
        photometry_group[f"{ii}"] = {
            "obsdate": f"{dd}",
            "flux": f"{mm}",
            "flux_error": f"{merr}",
            "flux_units": "1", # ABMag
            "filter_value": filt_code[ff],
            "instrument_value": "172", # ctio 4m decam
            #"limiting_flux": "",
            #"exptime": "",
            #"observer": "",
            #"comments": ""
          }
        ii += 1
    return {"photometry_group": photometry_group}

# JD = discovery time
# This creates a nice big dictionary with all the necessary info
# TO DO: Add an at_type parameter to adjust for the type of transient
def create_at_entry(ra, dec, JD, photometry_group, non_detection="", at_type="PSN", remarks="", internal_name="", related_files=""):
    ''' EXAMPLE
    ra, dec needs to be in degrees.
    JD: discovery JD YYYY-MM-DD.float or  float JD
    photometry_group: "photometry_group": {
          "0": {
            "obsdate": "2020-03-01.234",
            "flux": "19.5",
            "flux_error": "0.2",
            "limiting_flux": "",
            "flux_units": "1",
            "filter_value": "50",
            "instrument_value": "103",
            "exptime": "60",
            "observer": "Robot",
            "comments": ""
          },
          "1": {
            " obsdate ": "",
            " flux ": "",
            "flux_error": "",
            "limiting_flux": "",
            " flux_units ": "",
            " filter_value ": "",
            " instrument_value ": "",
            "exptime": "",
            "observer": "",
            "comments": ""
          }
    non_detection:"non_detection": {
        "obsdate": "2020-02-28.123",
        "limiting_flux": "21.5",
        "flux_units": "1",
        "filter_value": "50",
        "instrument_value": "103",
        "exptime": "60",
        "observer": "Robot",
        "comments": "",
        "archiveid": "",
        "archival_remarks": ""
      },
    related_files: "related_files": {
        "0": {
          "related_file_name": "rel_file_1.png",
          "related_file_comments": "Finding Chart..."
        },
        "1": {
          "related_file_name": "rel_file_2.jpg",
          "related_file_comments": "Discovery image..."

    '''
    entry = {}
    entry["ra"] = {
        "value": str(ra),
        "error": "",
        "units": "deg"
    }

    entry["dec"] = {
        "value": str(dec),
        "error": "",
        "units": "deg"
    }

    entry["reporting_group_id"]= "135"  # our DESIRT group id.
    entry["discovery_data_source_id"]="135"  # DESIRT
    entry["reporter"]= "Tomás Cabrera (CMU), Lei Hu (CMU), Igor Andreoni (UMD), Keerthi Kunnumkai (CMU), Brendan O’Connor (CMU), Antonella Palmese (CMU), on behalf of the GW-MMADS team"

    entry["discovery_datetime"]= f"{JD}"
    entry["at_type"] = at_types[at_type]
    entry["host_name"] = ""
    entry["host_redshift"] = ""
    entry["transient_redshift"] = ""
    entry["internal_name"] = internal_name
    # entry["internal_name_format"] = {
    #     "prefix": "prefixStr",
    #     "year_format": "YY",
    #     "postfix": "postfixStr"
    # }
    entry["remarks"] = remarks
    entry["photometry"] = photometry_group
    entry["related_files"] = related_files

    if non_detection == "":
        non_detection = {
            #"obsdate": "",
            #"limiting_flux": "",
            #"flux_units": "",
            #"filter_value": "",
            #"instrument_value": "",
            #"exptime": "",
            #"observer": "",
            #"comments": "",
            "archiveid": "0",  # other
            "archival_remarks": "DECam Legacy Survey",
        }
    entry["non_detection"] = non_detection

    #entry = json.dumps(entry, indent = 4)
    return entry

# Take output from above function and turn it into a json report
def create_at_json(entries):
    '''
    given a LIST of at entries defined in create_at_entry, create at json report numbered from 0 on
    '''
    ii = 0
    json_at = {"at_report":{}}
    for entry in entries:
        json_at["at_report"][f"{ii}"] = entry
        ii+=1
    return json_at

# function for changing data to json format
def format_to_json(source):
    # change data to json format and return
    parsed=json.loads(source,object_pairs_hook=OrderedDict)
    result=json.dumps(parsed,indent=4)
    return result


## ==============Below are functions taken from examples given on tns website============


# Disable print
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# function for sending json reports (AT or Classification)
def send_json_report(report):
    url=url_tns_api
    try:
        json_url=url+'/bulk-report'
        tns_marker=set_bot_tns_marker()
        headers={'User-Agent':tns_marker}
        # read json data from file
        json_read=format_to_json(open(report).read())
        # construct a dictionary of api key data and json data
        json_data={'api_key':api_key, 'data':json_read}
        print(f"json_data: \n\t{json_data}")
        # send json report using request module
        response=requests.post(json_url, headers=headers, data=json_data)
        # return response
        return response
    except Exception as e:
        return [None,'Error message : \n'+str(e)]

# sending tsv or json report (at or class) and printing reply
def send_report(report, type_of_report):
    url=url_tns_api
    # sending report and checking response
    print ("Sending "+report+" to the TNS...")
    # choose which function to call
    if type_of_report=="tsv":
        response=send_tsv_report(report)
    else:
        response=send_json_report(report)
    #response_check=check_response(response)
    print_status_code
    # if report is sent
    if response.status_code==200:
        print ("The report was sent to the TNS.")
        # report response as json data
        json_data=response.json()
        # taking report id
        report_id=str(json_data['data']['report_id'])
        print ("Report ID = "+report_id)
        # sending report id to get reply of the report
        # and printing that reply
        # waiting for report to arrive before sending reply
        # for report id
        blockPrint()
        counter = 0
        while True:
            time.sleep(SLEEP_SEC)
            reply_response=reply(report_id)
            print(reply_response)
            reply_res_check=check_response(reply_response)
            if reply_res_check!=False or counter >= LOOP_COUNTER:
                break
            counter += 1
            print(f"\tFinished check {counter}/{LOOP_COUNTER}")
        enablePrint()
        print_reply(report_id)
        return report_id
    else:
        print ("The report was not sent to the TNS.")
        return None


# function that checks response and
# returns True if everything went OK
# or returns False if something went wrong
def check_response(response):
    # if response exists
    if None not in response:
        # take status code of that response
        status_code=int(response.status_code)
        if status_code==200:
            # response as json data
            json_data=response.json()
            # id code
            id_code=str(json_data['id_code'])
            # id message
            id_message=str(json_data['id_message'])
            # print id code and id message
            print ("ID code = "+id_code)
            print ("ID message = "+id_message)
            # check if id code is 200 and id message OK
            if (id_code=="200" and id_message=="OK"):
                return True
            #special case
            elif (id_code=="400" and id_message=="Bad request"):
                return None
            else:
                return False
        else:
            return False
    else:
        # response doesn't exists, print error
        print (response[1])
        return False

# function for getting reply from report
def reply(report_id):
    url=url_tns_api
    try:
        # url for getting report reply
        reply_url=url+'/bulk-report-reply'
        tns_marker=set_bot_tns_marker()
        headers={'User-Agent':tns_marker}
        # construct a dictionary of api key data and report id
        reply_data={'api_key':api_key, 'report_id':report_id}
        # send report ID using request module
        response=requests.post(reply_url,headers=headers, data=reply_data)
        # return response
        return response
    except Exception as e:
        return [None,'Error message : \n\t'+str(e)]

def enablePrint():
    sys.stdout.close()
    sys.stdout = old_stdout

# sending report id to get reply of the report
# and printing that reply
def print_reply(report_id):
    url=url_tns_api
    # sending reply using report id and checking response
    print ("Sending reply for the report id "+report_id+" ...")
    reply_res=reply(report_id)
    reply_res_check=check_response(reply_res)
    # if reply is sent
    if reply_res_check==True:
        print ("The report was successfully processed on the TNS.\n")
        # reply response as json data
        json_data=reply_res.json()
        # feedback of the response
        print(111)
        print('json_data',json_data)
        feedback=list(find_keys('feedback',json_data))
        if len(feedback)==0:
            print('No \'feedback\' key in response json')
            return
        print(feedback,'feedback')
        # check if feedback is dict or list
        if type(feedback[0])==type([]):
            feedback=feedback[0]
        # go trough feedback
        for i in range(len(feedback)):
            # feedback as json data
            json_f=feedback[i]
            # feedback keys
            feedback_keys=list(json_f.keys())
            # messages for printing
            msg=[]
            # go trough feedback keys
            for j in range(len(feedback_keys)):
                key=feedback_keys[j]
                json_feed=json_f[key]
                msg=msg+print_feedback(json_feed)
            if msg!=[]:
                print ("-----------------------------------"\
                       "-----------------------------------" )
                for k in range(len(msg)):
                    print (msg[k][0])
                    #print (msg[k][1])
                print ("-----------------------------------"\
                       "-----------------------------------\n")
    else:
        print ("The report was not processed on the TNS because of the bad request(s).")

# find all occurrences of a specified key in json data
# and return all values for that key
def find_keys(key, json_data):
    if isinstance(json_data, list):
        for i in json_data:
            for x in find_keys(key, i):
                yield x
    elif isinstance(json_data, dict):
        if key in json_data:
            yield json_data[key]
        for j in list(json_data.values()):
            for x in find_keys(key, j):
                yield x

def print_feedback(json_feedback):
    # find all message id-s in feedback
    message_id=list(find_keys('message_id',json_feedback))
    # find all messages in feedback
    message=list(find_keys('message',json_feedback))
    # find all obj names in feedback
    objname=list(find_keys('objname',json_feedback))
    # find all new obj types in feedback
    new_object_type=list(find_keys('new_object_type',json_feedback))
    # find all new obj names in feedback
    new_object_name=list(find_keys('new_object_name',json_feedback))
    # find all new redshifts in feedback
    new_redshift=list(find_keys('new_redshift',json_feedback))
    # index counters for objname, new_object_type, new_object_name
    # and new_redshift lists
    n_o=0
    n_not=0
    n_non=0
    n_nr=0
    # messages to print
    msg=[]
    # go trough every message and print
    for j in range(len(message)):
        m=str(message[j])
        m_id=str(message_id[j])
        if m_id not in ['102','103','110']:
            if m.endswith('.')==False:
                m=m+'.'
            if m_id=='100' or  m_id=='101':
                m="Message = "+m+" Object name = "+str(objname[n_o])
                n_o=n_o+1
            elif m_id=='120':
                m="Message = "+m+" New object type = "+str(new_object_type[n_not])
                n_not=n_not+1
            elif m_id=='121':
                m="Message = "+m+" New object name = "+str(new_object_name[n_non])
                n_non=n_non+1
            elif m_id=='122' or  m_id=='123':
                m="Message = "+m+" New redshift = "+str(new_redshift[n_nr])
                n_nr=n_nr+1
            else:
                m="Message = "+m
            #msg.append(["Message ID = "+m_id,m])
            msg.append([m]) # Somewhat cluttered to include the message ID so I leave it out
    # return messages
    return msg

# Pass in a Pandas DataFrame with the following columns:
# Transient - Ra - Dec - FirstDetMJD - FirstDetMag - FirstDetMagErr - FirstDetFilt - NonDetMJD - NonDetLM - NonDetFilt - AT_Type - Remarks
# If needed, NonDet columns can be set to 0 and Remarks/AT_Type can be left blank (AT_Type will default to 1: PSN)
# For now this just allows for a single detection
def bulk_report(report_df):

    at_entries = []

    for i, row in report_df.iterrows():
        # Get all the necessary info from the current row of the DataFrame
        transient = row['Transient']
        ra = row['Ra']
        dec = row['Dec']
        jd = row['FirstDetJD']
        mag = row['FirstDetMag']
        magerr = row['FirstDetMagErr']
        filt = row['FirstDetFilt']
        #nodet_jd = row['NonDetJD']
        #nodet_lm = row['NonDetLM']
        #nodet_f = row['NonDetFilt']
        at_type = row['AT_Type']
        remarks = row['Remarks']
        
        """
        if tns_exist(ra,dec,radius=2):
            print(f"Transient already found within 2 arcsec of {transient}")
            continue
        else:
            print(f"Transient not already found within 2 arcsec of {transient}")
        """
        
        # Want remarks to be blank not NaN
        if pd.isna(remarks):
            remarks = ""
            
        # Want at_type to default to PSN
        if pd.isna(at_type):
            at_type = "PSN"

        # create non-detection
        nodet_jd = 0
        nodet_f = 0
        nodet_lm = 0
        non_det = non_detection(nodet_jd, nodet_f, nodet_lm)
        # create first detection photometry information
        photometry_group = create_photometry_group([jd], [mag], [magerr], [filt])
        # create bulk report entry for this object
        at_entry = create_at_entry(ra, dec, jd, photometry_group, non_det, at_type, remarks, internal_name=transient)
        
        at_entries.append(at_entry)

    # combine report information for multiple objects and save to text file.
    at_json = create_at_json(at_entries)

    # Make the file name unique to the specific time the report was made so we don't keep overwriting the same file
    report_txt_filename = f'/Users/brendan/Documents/research/DECam/TNS/GWMMADS/bulk_report_outfiles/{get_now_str()}_bulk_report.txt'

    with open(report_txt_filename, 'w') as outfile:
        json.dump(at_json, outfile,indent=4)
    print(json.dumps(at_json,indent=2))

    # send report to tns website.
    report_id = send_report(report=report_txt_filename, type_of_report='json')

    print("\n\nreply from TNS below:")
    print(json.loads(reply(report_id).content.decode("utf-8")))#['data']['feedback']