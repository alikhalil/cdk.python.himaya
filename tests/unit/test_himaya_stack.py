import aws_cdk as core
import aws_cdk.assertions as assertions

from himaya.himaya_stack import HimayaStack

# example tests. To run these tests, uncomment this file along with the example
# resource in himaya/himaya_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = HimayaStack(app, "himaya")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
