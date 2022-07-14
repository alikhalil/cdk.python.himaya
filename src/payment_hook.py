from common import *
from breaches import breaches
import requests


def handler(event, context):
    """handler function"""
    # pylint: disable=R0914,C0103,W0613

    if not event.get('httpMethod') == 'GET':
        error = {
            'statusCode': 422,
            'code': 'Invalid HTTP Method',
            'message': 'This lambda function only accepts the GET HTTP method.',
        }
        response_error(error)

    context_data = {
        'function_name': context.function_name,
        'function_version': context.function_version,
        'invoked_function_arn': context.invoked_function_arn,
        'memory_limit_in_mb': context.memory_limit_in_mb,
        'aws_request_id': context.aws_request_id,
        'log_group_name': context.log_group_name,
        'log_stream_name': context.log_stream_name,
    }

    # Log execution environment information
    LOGGER.info('Function: Payment Hook')
    LOGGER.info('### EVENT: {}'.format(serialize(event)))
    try:
        LOGGER.info('### BODY: {}'.format(
            serialize(json.loads(event.get('body')))))
    except:
        pass
    LOGGER.info('### CONTEXT: {}'.format(serialize(context_data)))

    # Parse the JSON payload containing order information
    order_data = json.loads(base64_decode(
        event.get('queryStringParameters').get('payload')))
    LOGGER.info("### Order Data: {}".format(serialize(order_data)))

    # Object to collect all information
    report_data = {}

    # Get breaches for any email addresses provided
    if 'email_addresses' in order_data:
        email_breaches = []
        # Process each email address in list
        for email_address in order_data.get('email_addresses'):
            email_breaches = get_breached_account(email_address)
            LOGGER.info("## BREACHES FOR {email}: {breaches}".format(
                email=email_address,
                breaches=serialize(email_breaches)
            ))
            report_data.update({email_address: []})

            for email_breach in email_breaches:
                # LOGGER.info("## FOUND BREACH: {}".format(serialize(email_breach)))
                report_data[email_address].append(
                    breaches.get(
                        email_breach.get('Name')
                    ))

    # Get breaches for any phone numbers provided
    if 'phone_numbers' in order_data:
        phone_breaches = []
        # LOGGER.info("## PHONE NUMBERS FOUND")
        for phone_number in order_data.get('phone_numbers'):
            LOGGER.info("## PHONE NUMBER: {}".format(phone_number))
            phone_breaches = get_breached_account(phone_number)
            LOGGER.info("## BREACHES FOR {phone_number}: {phone_breaches}".format(
                phone_number=phone_number,
                phone_breaches=serialize(phone_breaches)
            ))
            report_data.update({phone_number: []})

            for phone_breach in phone_breaches:
                # LOGGER.info("## FOUND BREACH: {}".format(serialize(phone_breach)))
                report_data[phone_number].append(
                    breaches.get(
                        phone_breach.get('Name')
                    ))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            'event': event,
            'order_data': order_data,
            'report_data': report_data,
            # 'base64_encoded_body': base64_encode(json.dumps(data)),
            # 'email_response': email_response,
            'context_data': context_data,
            'environment': dict(os.environ),
        })
    }


def get_breached_account(account):

    # Validate the email address
    if validateEmail(account) == validatePhoneNumber(account):
        LOGGER.info(
            '[get_breached_account] Account cannot be both email and phone number at the same time')
        return {
            'error': '[get_breached_account] Account cannot be both email and phone number at the same time',
        }

    url = 'https://haveibeenpwned.com/api/v3/breachedaccount/{account}'.format(
        account=account)
    headers = {
        # Remove hard coded api key and consider using AWS Secrets
        'hibp-api-key': '2c86226025514367970afa13e53525c4',
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent
        # User-Agent: <product>/<product-version> <comment>
        'User-Agent': 'BE_VIGILANT/v0.1 early_dev',
    }
    response = requests.get(url, headers=headers)

    return response.json()


if __name__ == "__main__":
    handler(None, None)
