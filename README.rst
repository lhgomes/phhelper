Python Handler Helper for Lambda
=====================================

.. image:: https://readthedocs.org/projects/phhelper/badge/?version=latest
   :target: https://phhelper.readthedocs.io/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.com/lhgomes/phhelper.svg?branch=master
    :target: https://travis-ci.com/lhgomes/phhelper

.. image:: https://badge.fury.io/py/phhelper.svg
    :target: https://badge.fury.io/py/phhelper
    
    
Overview
--------
Simplify best practice for Lambda in Python, handling Lambda events and errors with detailed and standarized logs.

Features
--------
* Dead simple to use, reduces the complexity of writing a Lambda with Python runtime
* Guarantees that Source will get a response even if an exception is raised
* Sends meaningful errors to Cloudwatch in the case of a failure
* Threading enables best runtime performance for events with multiple records
* JSON logging that includes request id's, event id's and source to assist in tracing logs relevant to a particular event

Installation
------------
Install into the root folder of your lambda function

.. code-block:: shell-session

   cd my-lambda-function/
   pip install phhelper -t .


Example Usage
-------------

.. code-block:: python

   from phhelper import aws_lambda_helper
   import json
   import time

   @aws_lambda_helper.handler
   def lambda_handler(event, context):
       context.logging.info('info_test')
       time.sleep(0.5)
       context.logging.error('error_test')
       time.sleep(0.5)
       context.logging.debug('debug_test')
       
       return {
           'statusCode': 200,
           'body': json.dumps('Hello from Lambda!')
       }

Threading
---------
If the event source send multiple records to be processed, you can enable Multithreading processing, by creating a 
Environment variable called ``THREADING_ENABLED`` with value ``TRUE``. This will make a loop into event records, starting a
thread for each record. Your handler will receive each record in a separeted call, inside a thread model.

Logging
--------
You can define the general log verbosity level using a Environment variable called ``LOG_LEVEL`` and the boto3 log level
using a Environment variable called ``BOTO_LOG_LEVEL``. 

The valid values for both Environment variables are:
* DEBUG
* INFO
* WARNING
* ERROR
* CRITICAL

The default values are:

.. code-block:: python

   LOG_LEVEL = 'ERROR'
   BOTO_LOG_LEVEL` = 'CRITICAL'

Credits
--------
Decorator implementation inspired by https://github.com/aws-cloudformation/custom-resource-helper

Log implementation inspired by https://gitlab.com/hadrien/aws_lambda_logging

Multiprocessing implementation inspired by https://medium.com/@urban_institute/using-multiprocessing-to-make-python-code-faster-23ea5ef996ba

License
--------
This library is licensed under the MIT License.
