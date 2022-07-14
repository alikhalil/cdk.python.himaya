from common import *


def handler(event, context):
    """handler function"""
    # pylint: disable=R0914,C0103,W0613

    if not event.get('httpMethod') == 'POST':
        error = {
            'statusCode': 422,
            'code': 'Invalid HTTP Method',
            'message': 'This lambda function only accepts the POST HTTP method.',
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

    data = json.loads(event['body'])
    item_value = 2.00
    promos = {
        '10OFF': 0.9,
        '15OFF': 0.85,
        '25OFF': 0.75,
    }
    selected_promo = 1.0
    count_emails = 0
    count_phone_numbers = 0

    LOGGER.info('Function: Register Order')
    LOGGER.info('### EVENT: {}'.format(serialize(event)))
    LOGGER.info('### BODY: {}'.format(
        serialize(json.loads(event.get('body')))))
    LOGGER.info('### CONTEXT: {}'.format(serialize(context_data)))

    # Validate the promo code
    if 'promo_code' in data:
        if (data['promo_code'] in promos):
            selected_promo = promos[data['promo_code']]
        else:
            error = {
                'statusCode': 422,
                'code': 'Invalid Promo Code',
                'message': 'The promo code ' + data['promo_code'] + ' is not valid.',
            }
            return response_error(error)
    else:
        selected_promo = 1.0

    # Validate the Billing Email
    if not validateEmail(data['billing_email']):
        error = {
            'statusCode': 422,
            'code': 'Invalid Email Address',
            'message': 'The Billing Email address {} is not valid.'.format(data['billing_email']),
        }
        return response_error(error)

    # Should only happen if email addresses are provided
    if 'email_addresses' in data:
        count_emails = len(data['email_addresses'])
        # Validate the email addresses
        for eml in data['email_addresses']:
            if not validateEmail(eml):
                error = {
                    'statusCode': 422,
                    'code': 'Invalid Email Address',
                    'message': 'The email address provided ' + eml + ' is not valid.',
                }
                LOGGER.info(error)
                return response_error(error)

    # Validate the phone numbers
    if 'phone_numbers' in data:
        count_phone_numbers = len(data['phone_numbers'])
        for phone_number in data['phone_numbers']:
            if not validatePhoneNumber(phone_number):
                error = {
                    'statusCode': 422,
                    'code': 'Invalid Mobile Number',
                    'message': 'The mobile number provided ' + phone_number + ' is not valid.',
                }
                return response_error(error)

    # Count email addresses and phone numbers to calculate bill amount
    total_amount = (count_emails + count_phone_numbers) * \
        item_value * selected_promo

    # Update the amount
    data.update({'amount': total_amount})

    # Send the registration confirmation and payment email
    email_response = sendEmail(data.get('billing_email'), serialize(data))

    response_body = json.dumps({
        'event': event,
        'data': data,
        'base64_encoded_body': base64_encode(json.dumps(data)),
        'email_response': email_response,
        'context_data': context_data,
        'environment': dict(os.environ),
    })

    return response_success(response_body)


if __name__ == "__main__":
    handler(None, None)
