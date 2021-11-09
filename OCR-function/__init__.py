import logging
import os

import azure.functions as func

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import os
import time
import json
import pyodbc
from datetime import datetime
from timeit import default_timer as timer
import requests

# Get the storage sas so it can be used in OCR process
storage_sas = '' # os.environ['storage_sas'] # SAS NOT CREATED #
storage_sas_url = "/?" + storage_sas

# Create SQL connection string
driver = '{ODBC Driver 17 for SQL Server}'
server = "ldebski-sql-server.database.windows.net,1433"
database = "ldebski-sql-db"
sql_username = "ldebski"
sql_password = '' # os.environ['sql_password'] # SQL DB NOT CREATED #
tabel_name = "ocr_processing_logging"
sqlConnectionString = f"Driver={driver};Server={server};Database={database};Uid={sql_username};\
    Pwd={sql_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Set the cognitive services variables
cs_subscription_key = '' # os.environ['cs_subscription_key'] # CS SERVICE NOT CREATED #
cs_params = {'language': 'en',
             'detectOrientation': 'false'}
cs_headers = {'Ocp-Apim-Subscription-Key' : cs_subscription_key,
              'Content-Type':'application/octet-stream' }
cs_endpoint = 'https://ldebski-computer-vision-standard.cognitiveservices.azure.com/'
ocr_url = f'{cs_endpoint}/vision/v3.2/read/analyze'

def ocr_call(inputfile):
    # Get Computer Vision Client with credentials
    computervision_client = ComputerVisionClient(
        cs_endpoint, CognitiveServicesCredentials(cs_subscription_key))

    # Call API with file bytes
    read_response = requests.post(ocr_url, data=inputfile.read(), headers=cs_headers, params=cs_params)

    # Get the operation location (URL with an ID at the end) from the response
    try:
        read_operation_location = read_response.headers['Operation-Location']
    except:
        raise Exception(read_response.text)

    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]

    # create sql connection while we wait for OCR results
    sqlConnection = pyodbc.connect(sqlConnectionString)
    sqlCursor = sqlConnection.cursor()

    # Call the "GET" API and wait for it to retrieve the results
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Print the detected text, line by line
    if read_result.status == OperationStatusCodes.succeeded:
        return read_result.analyze_result, sqlCursor
    else:
        return


def save_to_blob(outputfile, json_str):
    # Save json to blob storage
    outputfile.set(json_str)


def insert_log_info(run_timestamp, customer_id, filename, page_count,
                    file_operation_start_time, execution_legth, success, message, retry='0', sqlCursor=None):
    """
        This function inserts log information into SQL database.
        Schema:
        run_timestamp string,
        customer_id string,
        filename string,
        page_count int,
        file_operation_start_time string,
        execution_length float,
        success boolean,
        message string,
        retry boolean
    """
    if sqlCursor is None:
        sqlConnection = pyodbc.connect(sqlConnectionString)
        sqlCursor = sqlConnection.cursor()
    sqlCursor.execute(f"INSERT INTO {tabel_name} VALUES (?,?,?,?,?,?,?,?,?)", run_timestamp, customer_id,
                      filename, page_count, file_operation_start_time, execution_legth, success, message, retry)
    sqlCursor.commit()
    sqlCursor.close()


def get_file_path_info(document_name):
    document_splitted = document_name.split('/')
    return document_splitted[-1], document_splitted[-2]


def main(inputfile: func.InputStream, outputfile: func.Out[str]):
    start = timer()
    start_datetime = str(datetime.now())
    
    blob_uri = inputfile.uri

    # Extract information from file path
    file_name, customer_id = get_file_path_info(document_name=inputfile.name)

    # Check file extension is valid one
    if file_name.split('.')[-1].upper() not in ["JPEG", "PNG", "BMP", "PDF", "TIFF", "TIF", "JPG"]:
        # SQL SERVICE NOT CREATED
        # insert_log_info("", customer_id, file_name, 0, start_datetime,
        #                 timer() - start, 0, f"{customer_id}/{file_name} is not a supported format, will not send to OCR", 0)
        # SQL SERVICE NOT CREATED
        return

    # Create an OCR call and get results
    try:
        # OCR SERVICE NOT CREATED
        # results = ocr_call(inputfile)
        # OCR SERVICE NOT CREATED
        results = ({'randomdict': 'randomvalue'}, 'sqlcursor')
    except Exception as e:
        # SQL SERVICE NOT CREATED
        # insert_log_info("", customer_id, file_name, 0, start_datetime,
        #                 timer() - start, 0, str(e).replace("\n", "").replace('"', "'"), 0)
        # SQL SERVICE NOT CREATED
        return

    if results is None:
        # SQL SERVICE NOT CREATED
        # insert_log_info("", customer_id, file_name, 0, start_datetime,
        #                 timer() - start, 0, f"{customer_id}/{file_name} OCR failed to process this file", 0)
        # SQL SERVICE NOT CREATED
        return

    result, sqlCursor = results
    
    # Save result to blob storage as json file
    # RESULT FROM OCR PROCESS NOT CREATED
    # save_to_blob(outputfile, json.dumps(result.as_dict()))
    # RESULT FROM OCR PROCESS NOT CREATED
    save_to_blob(outputfile, json.dumps(result))

    # Write log information to SQL database
    # RESULT FROM OCR PROCESS NOT CREATED
    # page_count = len(result.read_results)
    # RESULT FROM OCR PROCESS NOT CREATED
    processing_time = timer() - start
    # SQL SERVICE NOT CREATED
    # insert_log_info("", customer_id, file_name, page_count, start_datetime,
    #                 processing_time, 1, "processed", 0, sqlCursor=sqlCursor)
    # SQL SERVICE NOT CREATED