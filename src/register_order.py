import logging
import os
import sys
import boto3
import json
import base64

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

    response_body = json.dumps({
        'event': event,
        # 'context': dict(context),
        'context_data': context_data,
        'environment': dict(os.environ),
    })

    return response_success(response_body)


def serialize(data):
    return json.dumps(
        data,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    )


def response_success(body):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "isBase64Encoded": False,
        "body": body,
    }


def response_error(error):
    return {
        "statusCode": error.status_code,
        "headers": {
            "Content-Type": "text/plain",
            "x-amzn-ErrorType": error.code
        },
        "isBase64Encoded": False,
        "body": error.code + ": " + error.message
    }


def validateEmail(email_address):
    # Source: https://www.abstractapi.com/guides/email-address-pattern-validation
    validationRegex = r'''^([-!#-'*+/-9 =?A-Z ^ -~]+(\.[-!  # -'*+/-9=?A-Z^-~]+)*|"([]!#-[^-~ \t]|(\\[\t -~]))+")@([0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?(\.[0-9A-Za-z]([0-9A-Za-z-]{0,61}[0-9A-Za-z])?)*|\[((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}|IPv6:((((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){6}|::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){5}|[0-9A-Fa-f]{0,4}::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){4}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):)?(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){3}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,2}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){2}|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,3}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,4}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,5}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3})|(((0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}):){0,6}(0|[1-9A-Fa-f][0-9A-Fa-f]{0,3}))?::)|(?!IPv6:)[0-9A-Za-z-]*[0-9A-Za-z]:[!-Z^-~]+)])$'''
    return validationRegex.test(email_address)


def validatePhoneNumber(phone_number):
    validationRegexPhone = r'^\+[0-9]+$'
    return validationRegexPhone.test(phone_number)


def base64_encode(data):
    urlSafeEncodedBytes = base64.urlsafe_b64encode(data.encode("utf-8"))
    urlSafeEncodedStr = str(urlSafeEncodedBytes, "utf-8")
    return urlSafeEncodedStr


def base64_decode(encodedStr):
    decodedBytes = base64.urlsafe_b64decode(encodedStr)
    decodedStr = str(decodedBytes, "utf-8")
    return decodedStr


def getHtmlContent(email, message):
    return '''
        <html>
        <body>
            <h1>Order request received!</h1>
            <p>An order has been received with billing_email as {email}. Please vist the below URL to pay for the services after which you will received the report immediately.</p>
            <ul>
            <li style="font-size:18px">✉️ <b>{email}</b></li>
            </ul>
            <p style="font-size:18px"><pre>{message}</pre></p>
        </body>
        </html>
    '''.format(email=email, message=message)


def getTextContent(email, message):
    return '''
        Received an Email. 📬
        Sent from:
            ✉️ {email}
        {message}
    '''.format(email=email, message=message)


if __name__ == "__main__":
    handler(None, None)
