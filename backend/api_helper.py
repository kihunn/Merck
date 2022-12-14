from flask import make_response, json
import pandas as pd
import qr_code
from datetime import datetime, date
import db_helper
from print_helper import print_image
from qr_code import convert_image_to_base64


############################################################
# Function_name: create_response
#
# Function_logic:
# Utilises the make_response function from flask (Check flask documentation for more info)
#
#
# Arguments: 
#    - message (default is ''): Message that we would like to return to our client (Should be in string format)
#    - status_code (default is 200): Indication of whether clients request suceeded, e.g 200, 400, 404
#    -mimetype (default is JSON): mimetype of the content that we are returning to the client
# Return:
#    - response: Response object created from make_response function for us to return response to users.
############################################################
def create_response(message='',status_code=200, mimetype='application/json'):
        response = make_response(message)
        response.status_code = status_code
        response.mimetype = mimetype
        return response

def create_response_from_scanning(message="", status_code=200, mimetype='application/json'):
        response = make_response(json.dumps(message))
        response.status_code = status_code
        response.mimetype = mimetype
        return response


############################################################
# Function_name: insert_new_sample
#
# Function_logic:
# Inserts newly retrieved sample (both from CSV and input form) into our data base.
# Currently it overrites existing data, depends on what Terri wants in terms of duplicate entries
#
# Arguments: 
#    - qr_code_key: Unique identifier for each sample. qr_code_key is the Primary Key of each sample in DB
#    - sample_obj: Obj containing key-value pair of information regarding each sample
# Return:
#    - Bool: Returns True/False on whether our insertion was a duplicate or unique
############################################################
def insert_new_sample(qr_code_key,sample_obj):
    #Checks if this qr_code_key created already exists in our DB. Returns True if exists
    exists = db_helper.check_if_key_exists(qr_code_key)
    #Updates existing sample if qr_code exists in our DB
    if exists:
            db_helper.update_sample_by_qr_code_key(qr_code_key, sample_obj)
            return False
    #If sample inserting to DB is unique
    else:
        db_helper.insert_new_sample(qr_code_key,sample_obj)

    return True
    

############################################################
# Function_name: retrieve_sample_information_with_key
#
# Function_logic:
# Inserts newly retrieved sample (both from CSV and input form) into our data base.
# Currently it overrites existing data, depends on what Terri wants in terms of duplicate entries
#
# Arguments: 
#    - qr_code_key: Unique identifier for each sample. qr_code_key is the Primary Key of each sample in DB
#
# Return:
#    - return_dic: All columns of sample in the DB
############################################################
def retrieve_sample_information_with_key(qr_code_key):
        return_dic = {}
        qr_code_key = str(qr_code_key)

        res = db_helper.retrieve_sample_information_with_key(qr_code_key)
        print(f"QR KEY IS {qr_code_key}")
        # if qr_code_key does not exist in DB
        if not res:
                return {}, 404

        else: # qr_code_key exists in DB
                content = res # if res is None, it will say invalid index
        
                return_dic = {
                        'qr_code_key': content.qr_code_key,
                        'experiment_id': content.experiment_id,
                        'storage_condition': content.storage_condition,
                        'analyst': content.analyst,
                        'contents': content.contents,
                        'date_entered': content.date_entered,
                        'date_modified': content.date_modified,
                        'expiration_date': content.expiration_date
                }

        return return_dic, 200


############################################################
# Function_name: parse_csv_to_db
#
# Function_logic:
# This function is called to parse a CSV uploaded and insert each column of the CSV
# into our DB.
#
# Arguments: 
#    - file_path: The path of the uploaded CSV file that we stored in ../csv
#    - info: info is an array [new_insert_count, updated_insert_count]
#            -> This code just returns to our front-end how many of the rows in the CSV that
#               we inserted into our DB were duplicate or Unique. (Can be removed)
#
# Return:
#    - Status-Code: 200 if successful, 500 if unsuccessful
############################################################
def parse_csv_to_db(file_path,info):
        try:
                return_dic = {}
                df = pd.read_csv(file_path)
                current_date = db_helper.get_strf_utc_date()
                for index,row in df.iterrows():

                        #Convert dataframe rows into a JSON obj (dictionary)
                        dic = {
                                'experiment_id': row['experiment_id'],
                                'storage_condition': row['storage_condition'],
                                'analyst': row['analyst'],
                                'contents': row['contents'],
                                'date_entered': row['date_entered'],
                                'expiration_date': row['expiration_date'],
                                'date_modified': current_date,
                        }

                        qr_code_key, base64_hash = qr_code.create_qr_code_without_saving(dic)
                        base64_hash = base64_hash
                        return_dic[qr_code_key] = base64_hash
                        #If we are inserting a new_sample, we update new_sample_insert count
                        if insert_new_sample(qr_code_key, dic):
                                info[0] += 1
                        #If we are inserting an exisiting sample, we update updated_insert_count
                        else:
                                info[1] += 1

                return 200, return_dic
        except Exception as e:
                print(e, flush=True)
                return 500, None



def print_label_with_qr_code_key(qr_code_key, size='2ml'):
        dic, _ = retrieve_sample_information_with_key(qr_code_key)
        dic['size'] = size
        img = qr_code.create_qr_code_return_image_obj(dic)
        return print_image(img)


def retrieve_label_with_qr_code_key(qr_code_key):
        dic, status = retrieve_sample_information_with_key(qr_code_key)
        # print(dic, status, flush=True)
        if status != 200:
                return None

        img = qr_code.create_qr_code_return_image_obj(dic)
        img = img.rotate(angle=270, expand=True)
        return convert_image_to_base64(img)     