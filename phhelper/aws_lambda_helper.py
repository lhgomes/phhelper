import os
import json
import logging
import traceback
from . import aws_lambda_logging
from functools import wraps

def __get_log_level(env_name='LOG_LEVEL', default_level='ERROR'):
    log_level = str(os.environ.get(env_name,default_level)).upper()
    if log_level not in [ 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' ]:
        log_level = default_level

    return log_level

def __setup_log(context):
    aws_lambda_logging.setup(level=log_level, boto_level=boto_level,
                            function_arn=context.invoked_function_arn,
                            aws_request_id=context.aws_request_id)    

def __setup_cognito_log(event,context):
    aws_lambda_logging.setup(level=log_level, boto_level=boto_level,
                             function_arn=context.invoked_function_arn,
                             aws_request_id=context.aws_request_id,
                             cognito_region=event['region'],
                             cognito_userPoolId=event['userPoolId'],
                             cognito_triggerSource=event['triggerSource'])  

def __setup_events_log(event,context):
    aws_lambda_logging.setup(level=log_level, boto_level=boto_level,
                             function_arn=context.invoked_function_arn,
                             aws_request_id=context.aws_request_id,
                             event_source=event['source'],
                             event_time=event['time'],
                             event_detail_type=event['detail-type'])  
    
def __setup_api_log(event,context):
    aws_lambda_logging.setup(level=log_level, boto_level=boto_level,
                            function_arn=context.invoked_function_arn,
                            aws_request_id=context.aws_request_id,
                            api_request_id=event['requestContext']['requestId'],
                            api_path=event['requestContext']['path'])      

def __setup_multi_log(event,context):
    aws_lambda_logging.setup(level=log_level, boto_level=boto_level,
                            function_arn=context.invoked_function_arn,
                            aws_request_id=context.aws_request_id,
                            event_source=event['eventSource'],
                            event_source_arn=event['eventSourceARN'])      

# Threaded function for processing.
def __multi_record_process(f, thread_num, record, context):
    try:
        __setup_multi_log(record,context)
        logging.info('Running thread: %s' % (thread_num))
        logging.debug(record)
        
        f(record, context)
        
        return True
    except Exception as error:
        logging.error('Error with record processing')
        raise error

def __thread_records_handler(f, event, context):
    import multiprocessing
    try:
        logging.debug(("CPU count: %s") % (multiprocessing.cpu_count()))
        
        records = event['Records']
        num_records = len(records)
        logging.info(("Event record count: %s") % (num_records))
        
        processes = []
        for i in range(num_records):
            p = multiprocessing.Process(target=__multi_record_process, args=(f, i, records[i], context,))
            processes.append(p)
            p.start()
            
        for process in processes:
            process.join()
    
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        raise error

    return True

def __records_handler(f, event, context):
    try:
        for record in event['Records']:
            f(record, context)
            
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        raise error

    return True

def __cognito_handler(f, event, context):
    result = None
    try:
        __setup_cognito_log(event,context)

        result = f(event, context)
        
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        raise error
    finally:
        logging.debug(result)
        
    return result

def __events_handler(f, event, context):
    result = None
    try:
        __setup_events_log(event,context)

        result = f(event, context)
        
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        raise error
    finally:
        logging.debug(result)
        
    return result

def __apigateway_handler(f, event, context):
    result = None
    try:
        __setup_api_log(event,context)

        result = f(event, context)
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        result = {
            'statusCode': 412,
            'body': json.dumps({'message': str(error)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        } 
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        result = {
            'statusCode': 500,
            'body': json.dumps({'message': str(error)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    finally:
        logging.debug(result)
    
    return result

log_level = __get_log_level('LOG_LEVEL')
boto_level = __get_log_level('BOTO_LOG_LEVEL','CRITICAL')

def handler(f):
    @wraps(f)
    def generic_handler(event, context):
        __setup_log(context)
        logging.debug(event)
    
        context.logging = logging
        if 'Records' in event:
            thread_enabled = str(os.environ.get('THREADING_ENABLED','FALSE')).upper()
            if (thread_enabled == 'TRUE'):
                __thread_records_handler(f, event, context)
            else:
                __records_handler(f, event, context)
        elif 'requestContext' in event:
            return __apigateway_handler(f, event, context)
        elif 'source' in event and event['source'] == 'aws.events':
            return __events_handler(f, event, context)
        elif 'userPoolId'  in event:
            return __cognito_handler(f, event, context)
        else:
            logging.error('Unmapped event source')
            raise Exception('Unmapped event source')
            
    return generic_handler
