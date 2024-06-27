import os
import json
import logging
from . import aws_lambda_logging
from functools import wraps
from traceback import format_exception

def __get_log_level(env_name='LOG_LEVEL', default_level='ERROR'):
    log_level = str(os.environ.get(env_name,default_level)).upper()
    if log_level not in [ 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' ]:
        log_level = default_level

    return log_level

def __log_error(error):
    logging.error({
        "type": type(error).__name__, 
        "message": error, 
        "at": format_exception(error)
    })

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

def __default_handler(f, event, context):
    result = None
    try:
        result = f(event, context)
            
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        __log_error(error)
        raise error
    finally:
        logging.debug(result)
        
    return result

# Threaded function for processing.
def __multi_record_process(f, thread_num, record, context):
    try:
        __setup_multi_log(record,context)
        logging.info('Running thread: %s' % (thread_num))
        logging.debug(record)
        
        f(record, context)
        
        return True
    except Exception as error:
        __log_error(error)
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
        __log_error(error)
        raise error

    return True

def __batch_handler(f, event, context):
    result = None
    try:
        result = f(event, context)
            
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        __log_error(error)
        raise error
    finally:
        logging.debug(result)
        
    return result

def __records_handler(f, event, context):
    try:
        for record in event['Records']:
            f(record, context)
            
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        __log_error(error)
        raise error

    return True

def __partial_batch_records_handler(f, event, context):
    batch_item_failures = []

    for record in event['Records']:
        try:
            f(record, context)
        except Exception as error:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            __log_error(error)

    if len(batch_item_failures) > 0:
        logging.critical(f'Batch item failures: {batch_item_failures}')
        return { 'batchItemFailures': batch_item_failures }
    else:
        logging.info(f'Processed records: {len(event["Records"])}')
        return None
    
def __cognito_handler(f, event, context):
    result = None
    try:
        __setup_cognito_log(event,context)

        result = f(event, context)
        
    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        raise error
    except Exception as error:
        __log_error(error)
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
        __log_error(error)
        raise error
    finally:
        logging.debug(result)
        
    return result

def __apigateway_handler(f, event, context):
    result = None
    try:
        __setup_api_log(event,context)

        add_default_headers = str(os.environ.get('ADD_DEFAULT_HEADERS', 'FALSE')).upper()

        result = f(event, context)
        if add_default_headers == 'TRUE':
            if not 'headers' in result:
                result['headers'] = {}

            if not 'Content-Type' in result['headers']:
                result['headers']['Content-Type'] = 'application/json'

            if not 'Access-Control-Allow-Origin' in result['headers']:
                result['headers']['Access-Control-Allow-Origin'] = '*'

    except AssertionError as error:
        logging.info('lambda_handler assert: %s' % (error))
        result = {
            'statusCode': 400,
            'body': json.dumps({'message': str(error)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        } 
    except Exception as error:
        __log_error(error)
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
                partial_batch_response = str(os.environ.get('PARTIAL_BATCH_RESPONSE','FALSE')).upper()
                if (partial_batch_response == 'TRUE'):
                    return __partial_batch_records_handler(f, event, context)
                else:
                    batch_request = str(os.environ.get('BATCH_REQUEST','FALSE')).upper()
                    if (batch_request == 'TRUE'):
                        return __batch_handler(f, event, context)
                    else:
                        __records_handler(f, event, context)
        elif 'requestContext' in event:
            return __apigateway_handler(f, event, context)
        elif 'source' in event and event['source'] == 'aws.events':
            return __events_handler(f, event, context)
        elif 'userPoolId'  in event:
            return __cognito_handler(f, event, context)
        else:
            logging.warning('Unmapped event source. Using the default event handler.')
            return __default_handler(f, event, context)
            
    return generic_handler
