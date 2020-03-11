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