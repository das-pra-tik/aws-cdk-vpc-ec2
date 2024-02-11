import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_vpc_ec2.cdk_vpc_ec2_stack import CdkVpcEc2Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_vpc_ec2/cdk_vpc_ec2_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkVpcEc2Stack(app, "cdk-vpc-ec2")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
