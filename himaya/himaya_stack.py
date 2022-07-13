from enum import auto
from http import server
from sys import path
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_logs as logs,
    aws_s3 as s3,
    aws_iam as iam,
    aws_s3_deployment as s3deployment,
    aws_lambda as lambda_,
    aws_apigateway as apigateway,
)
from constructs import Construct


# Move these into its own file
SES_DOMAIN = 'himaya.tech'
SES_EMAIL_FROM = 'no-reply@himaya.tech'
SES_EMAIL_TO = 'ali.khalil@gmail.com'
SES_REGION = 'eu-west-1'


class HimayaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for Website Logs
        s3_website_logs = s3.Bucket(self, "WebsiteLogs",
                                    versioned=False,
                                    removal_policy=RemovalPolicy.DESTROY,
                                    auto_delete_objects=True,
                                    encryption=s3.BucketEncryption.S3_MANAGED,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                    )

        # S3 Bucket for Static Website Assets
        s3_static_website = s3.Bucket(self, "StaticWebsiteAssets",
                                      bucket_name='www.himaya.tech',
                                      versioned=False,
                                      removal_policy=RemovalPolicy.DESTROY,
                                      auto_delete_objects=True,
                                      access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                      encryption=s3.BucketEncryption.S3_MANAGED,
                                      server_access_logs_bucket=s3_website_logs,
                                      public_read_access=True,
                                      website_error_document='404.html',
                                      website_index_document='index.html',
                                      )

        # Add Policy to the static website S3 bucket
        s3_static_website.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                principals=[iam.AnyPrincipal()],
                resources=["arn:aws:s3:::www.himaya.tech/*"],
                conditions={
                    "IpAddress": {
                        "aws:SourceIp": [
                            "2400:cb00::/32", "2405:8100::/32", "2405:b500::/32", "2606:4700::/32",
                            "2803:f800::/32", "2a06:98c0::/29", "2c0f:f248::/32", "103.21.244.0/22",
                            "103.22.200.0/22", "103.31.4.0/22", "104.16.0.0/13", "104.24.0.0/14",
                            "108.162.192.0/18", "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
                            "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20", "190.93.240.0/20",
                            "197.234.240.0/22", "198.41.128.0/17"
                        ]
                    }
                }
            )
        )

        # Deploy assets to Static Website Bucket
        s3_deploy_assets = s3deployment.BucketDeployment(self, "DeployWebsiteAssets",
                                                         sources=[s3deployment.Source.asset(
                                                             './website-dist')],
                                                         destination_bucket=s3_static_website,
                                                         )

        # Redirect naked domain to www subdomain
        s3_redirect_naked_domain = s3.Bucket(self, "NakedDomainRedirect",
                                             bucket_name='himaya.tech',
                                             versioned=False,
                                             removal_policy=RemovalPolicy.DESTROY,
                                             auto_delete_objects=True,
                                             access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
                                             encryption=s3.BucketEncryption.S3_MANAGED,
                                             server_access_logs_bucket=s3_website_logs,
                                             public_read_access=True,
                                             website_redirect=s3.RedirectTarget(
                                                 host_name='www.himaya.tech',
                                                 protocol=s3.RedirectProtocol.HTTPS,
                                             ),
                                             )

        # Register an order
        fn_register_order = lambda_.Function(self, "RegisterOrder",
                                             code=lambda_.Code.from_asset(
                                                 "./src"),
                                             handler="register_order.handler",
                                             runtime=lambda_.Runtime.PYTHON_3_9,
                                             architecture=lambda_.Architecture.ARM_64,
                                             memory_size=512,
                                             timeout=Duration.seconds(10),
                                             insights_version=lambda_.LambdaInsightsVersion.VERSION_1_0_135_0,
                                             log_retention=logs.RetentionDays.ONE_WEEK,
                                             environment={
                                                 'BUCKET': s3_static_website.bucket_name,
                                             },
                                             )

        # Process payment hook
        fn_payment_hook = lambda_.Function(self, "PaymentHook",
                                           code=lambda_.Code.from_asset(
                                               "./src"),
                                           handler="payment_hook.handler",
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           architecture=lambda_.Architecture.ARM_64,
                                           memory_size=512,
                                           timeout=Duration.seconds(10),
                                           insights_version=lambda_.LambdaInsightsVersion.VERSION_1_0_135_0,
                                           log_retention=logs.RetentionDays.ONE_WEEK,
                                           environment={
                                               'BUCKET': s3_static_website.bucket_name,
                                           },
                                           )

        # Add permissions to the Lambda function to send Emails
        policy_send_email = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'ses:SendEmail',
                'ses:SendRawEmail',
                'ses:SendTemplatedEmail',
            ],
            resources=[
                'arn:aws:ses:{SES_REGION}:{ACCOUNT_ID}:identity/{SES_EMAIL_FROM}'.format(
                    SES_REGION=SES_REGION, SES_EMAIL_FROM=SES_EMAIL_FROM, ACCOUNT_ID=Stack.of(self).account),
                'arn:aws:ses:{SES_REGION}:{ACCOUNT_ID}:identity/{SES_EMAIL_TO}'.format(
                    SES_EMAIL_TO=SES_EMAIL_TO, SES_REGION=SES_REGION, ACCOUNT_ID=Stack.of(self).account),
                'arn:aws:ses:{SES_REGION}:{ACCOUNT_ID}:identity/{SES_DOMAIN}'.format(
                    SES_REGION=SES_REGION, SES_DOMAIN=SES_DOMAIN, ACCOUNT_ID=Stack.of(self).account),
            ],
        )

        fn_register_order.add_to_role_policy(policy_send_email)

        # Log Group for API Gateway Logs storage
        log_group_apigateway = logs.LogGroup(self, "LogGroupapigateway",
                                             removal_policy=RemovalPolicy.DESTROY,
                                             )

        # API Gateway
        apigateway_backend = apigateway.RestApi(self, "ApiGateway",
                                                deploy_options=apigateway.StageOptions(
                                                    stage_name="beta",
                                                    metrics_enabled=True,
                                                    logging_level=apigateway.MethodLoggingLevel.INFO,
                                                    data_trace_enabled=True,
                                                    access_log_destination=apigateway.LogGroupLogDestination(
                                                        log_group_apigateway),
                                                    access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                                                        caller=True,
                                                        http_method=True,
                                                        ip=True,
                                                        protocol=True,
                                                        request_time=True,
                                                        resource_path=True,
                                                        response_length=True,
                                                        status=True,
                                                        user=True,
                                                    ),
                                                    method_options={
                                                        '/*/*': apigateway.MethodDeploymentOptions(
                                                            throttling_rate_limit=10,
                                                            throttling_burst_limit=20
                                                        )
                                                    }
                                                )
                                                )

        # Add API Gateway resources and associate the methods with Lambda Functions
        api_resource_register = apigateway_backend.root.add_resource(
            'register')
        api_resource_register.add_method(
            "POST", apigateway.LambdaIntegration(fn_register_order))
        api_resource_payment = apigateway_backend.root.add_resource('payment')
        api_resource_payment.add_method(
            "GET", apigateway.LambdaIntegration(fn_payment_hook))

        #     new CfnOutput(this, 'WebsiteUrl', { value: static_website_bucket.bucketWebsiteUrl });
        CfnOutput(self, 'WebsiteUrl',
                  value=s3_static_website.bucket_website_url,
                  )
