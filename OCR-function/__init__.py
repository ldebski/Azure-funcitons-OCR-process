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

# Get the storage sas so it can be used in OCR process
storage_sas = os.environ['storage_sas']
storage_sas_url = "/?" + storage_sas

# Create SQL connection string for information logging
# Azure functions come with pre-installed ODBC driver that we can use
# https://github.com/Azure/azure-functions-docker/blob/dev/host/3.0/buster/amd64/python/python37/python37.Dockerfile#L52
driver = '{ODBC Driver 17 for SQL Server}'
server = "SQL-SERVER-NAME"
database = "SQL-DATABASE-NAME"
sql_username = "SQL-USER-NAME"
sql_password = os.environ['sql_password']
tabel_name = "SQL-TABLE-NAME"
sqlConnectionString = f"Driver={driver};Server={server};Database={database};Uid={sql_username};\
    Pwd={sql_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Set the cognitive services variables
cs_subscription_key = os.environ['cs_subscription_key']
cs_params = {'language': 'en',
             'detectOrientation': 'false'}
cs_headers = {'Ocp-Apim-Subscription-Key': cs_subscription_key,
              'Content-Type': 'application/octet-stream'}
cs_endpoint = 'COMPUTER-SERVICE-ENDPOINT'
ocr_url = f'{cs_endpoint}/vision/v3.2/read/analyze'


def ocr_call(blob_uri):
    # Get Computer Vision Client with credentials
    computervision_client = ComputerVisionClient(
        cs_endpoint, CognitiveServicesCredentials(cs_subscription_key))

    # Call API with URL and raw response (allows you to get the operation location)
    read_response = computervision_client.read(
        blob_uri+storage_sas_url, raw=True, custom_headers=cs_params)

    # Get the operation location (URL with an ID at the end) from the response
    try:
        read_operation_location = read_response.headers['Operation-Location']
    except:
        raise Exception(read_response.text)

    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]

    # Call the "GET" API and wait for it to retrieve the results
    # This operation can take a while (few seconds)
    # If you want you can try to speed up Azure Function by doing something in a meanwhile e.g. create SQL connections
    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Print the detected text, line by line
    if read_result.status == OperationStatusCodes.succeeded:
        return read_result.analyze_result
    else:
        return


def save_to_blob(outputfile, json_str):
    # Save json to blob storage
    outputfile.set(json_str)


def insert_log_info(filename, page_count,
                    file_operation_start_time, execution_legth, success, message):
    """
        This function inserts log information into SQL database.
        Schema:
        filename string,
        page_count int,
        file_operation_start_time string,
        execution_length float,
        success boolean,
        message string
    """
    sqlConnection = pyodbc.connect(sqlConnectionString)
    sqlCursor = sqlConnection.cursor()
    sqlCursor.execute(f"INSERT INTO {tabel_name} VALUES (?,?,?,?,?,?,?,?,?)",
                      filename, page_count, file_operation_start_time, execution_legth, success, message)
    sqlCursor.commit()
    sqlCursor.close()


def main(inputfile: func.InputStream, outputfile: func.Out[str]):
    # Get current time for logging purposes
    start = timer()
    start_datetime = str(datetime.now())

    # Get file information
    blob_uri = inputfile.uri
    file_name = inputfile.name

    # Check file extension is valid one
    if file_name.split('.')[-1].upper() not in ["JPEG", "PNG", "BMP", "PDF", "TIFF", "TIF", "JPG"]:
        insert_log_info(file_name, 0, start_datetime,
                        timer() - start, 0, f"{file_name} is not a supported format, will not send to OCR")
        return

    # Create an OCR call and get results
    try:
        results = ocr_call(blob_uri)
    except Exception as e:
        insert_log_info(file_name, 0, start_datetime,
                        timer() - start, 0, str(e).replace("\n", "").replace('"', "'"))
        return

    if results is None:
        insert_log_info(file_name, 0, start_datetime,
                        timer() - start, 0, f"{file_name} OCR failed to process this file")
        return

    result = results

    # Save result from OCR to blob storage as json file
    save_to_blob(outputfile, json.dumps(result.as_dict()))

    # Write log information to SQL database
    page_count = len(result.read_results)
    processing_time = timer() - start
    insert_log_info(file_name, page_count, start_datetime,
                    processing_time, 1, "processed", )
