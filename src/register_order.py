import logging
import os
import sys
import boto3
import json

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Move these into its own file
SES_DOMAIN = 'himaya.tech'
SES_EMAIL_FROM = 'no-reply@himaya.tech'
SES_EMAIL_TO = 'ali.khalil@gmail.com'
SES_REGION = 'eu-west-1'


def handler(event, context):
    """handler function"""
    # pylint: disable=R0914,C0103,W0613

    LOGGER.info('Function: Register Order')
    LOGGER.info('### EVENT: {}'.format(serialize(event)))
    LOGGER.info('### CONTEXT: {}'.format(type(context)))
    # LOGGER.info('### CONTEXT: {}'.format(serialize(dict(context))))
    # LOGGER.info('### CONTEXT: {}'.format(serialize(context)))

    context_data = {
        'function_name': context.function_name,
        'function_version': context.function_version,
        'invoked_function_arn': context.invoked_function_arn,
        'memory_limit_in_mb': context.memory_limit_in_mb,
        'aws_request_id': context.aws_request_id,
        'log_group_name': context.log_group_name,
        'log_stream_name': context.log_stream_name,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            'event': event,
            # 'context': dict(context),
            'context_data': context_data,
            'environment': dict(os.environ),
        })
    }


def serialize(data):
    return json.dumps(
        data,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )


if __name__ == "__main__":
    handler(None, None)
