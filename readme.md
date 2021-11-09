# Azure OCR process using Azure Function - Python

This is an Azure Function repo for [Azure Optical Character Recognition](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/overview-ocr) using Azure [Read API](https://centraluseuap.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-2/operations/5d986960601faab4bf452005).


## How it works

The function uses [Blob Storage binding](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-storage-blob) on input and output and thanks to that this function is triggered on every new file appearing in specified storage folder. Results of OCR process is saved as json file in a specified output folder. Those paths can be found inside `OCR-function/function.json` file, which contains all function binding.

For every file processed logging information is saved inside SQL database with information whether OCR process succeeded or not if some exception is caught e.g. wrong file extension, empty file.

If this function fails and an exception won't be caught, by default Azure Function will retry this operation 5 times and then add information about this fail on top of Poison Queue. Read more in [here](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-error-pages?tabs=csharp)

## Set up

This function requires few additional resources to work:
- Azure Storage Account - place for input/output files to be saved and for automatically created message queue for new files
- SQL Database - for logging information
- Azure Computer Services - necessary for OCR process

All of those resources require some sort of authentication to be used. Those are passed via environmental variables, which can be added to Azure Function App inside Configuration settings. List of environmental variables used:
- sql_password - Password for SQL server
- storage_sas - SAS generated for input folder. Files send to OCR needs to be authenticated, so SAS is added to file URL.
- cs_subscription_key - Computer Service subscription key
- ocrstorageaccountdemo_STORAGE - Storage Account Connection string

Those variables are used in `OCR-function/__init__.py` or in `OCR-function/function.json` files.

Additionally all python libraries needed are specified in `requirements.txt` file. 

## Additional information

I highly recommend using [Visual Studio Code to work with Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=csharp), as it makes life much easier. It automatically creates necessary Azure services to run Azure Function, helps with creating new function or bindings and allows us to test our functions locally with ease.

