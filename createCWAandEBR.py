import json
import boto3

def describe_instances_with_tags(ec2_client, instance_id):
    try:
        # Retrieve instances with the specified tags
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Project', 'Values': ['Castle']},
                {'Name': 'instance-id', 'Values': [instance_id]}
            ]
        )
        return response
    
    except Exception as e:
        raise Exception(f'Error retrieving Instance with Specific Tags: {str(e)}')

def create_cloudwatch_alarm(cloudwatch_client, instance_id):
    try:
        # Create CloudWatch alarm for CPU utilization
        alarm_name = f'EC2Alarm-{instance_id}'
        alarm_actions = ['arn:aws:sns:us-east-1:XXXXXXXXXXXX:SNS']  # SNS Topic ARN

        cloudwatch_client.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription='Monitor EC2 based on CPU Utilization',
            ActionsEnabled=True,
            AlarmActions=alarm_actions,
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Statistic='Average',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            Period=3600,  # 1 hour
            EvaluationPeriods=1,
            Threshold=5,
            ComparisonOperator='LessThanThreshold'
        )
        return alarm_name

    except Exception as e:
        raise Exception(f'Error creating CloudWatch Alarm: {str(e)}')

def create_cloudwatch_event_rule(events_client, instance_id, alarm_name):
    try:
        # Create the CloudWatch Event Rule
        rule_name = f'CloudWatchEventRule-{instance_id}'
        rule_description = 'Trigger Lambda function when CloudWatch alarm enters ALARM state'
        rule_pattern = {
            "source": ["aws.cloudwatch"],
            "detail-type": ["CloudWatch Alarm State Change"],
            "detail": {
                "alarmName": [alarm_name],
                "state": {
                    "value": ["ALARM"]
                }
            }
        }
        rule_targets = [{"Arn": "arn:aws:lambda:us-east-1:XXXXXXXXXXXX:function:XXXXXXXXXXXX", "Id": "TargetFunction"}]

        events_client.put_rule(
            Name=rule_name,
            Description=rule_description,
            EventPattern=json.dumps(rule_pattern),
            State="ENABLED"
        )

        events_client.put_targets(
            Rule=rule_name,
            Targets=rule_targets
        )
        return rule_name

    except Exception as e:
        raise Exception(f'Error creating CloudWatch Event Rule: {str(e)}')

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    cloudwatch_client = boto3.client('cloudwatch')
    events_client = boto3.client('events')
    instance_id = event['InstanceID']

    try:
        response = describe_instances_with_tags(ec2_client, instance_id)
        print(response)

        if response['Reservations']:
            alarm_name = create_cloudwatch_alarm(cloudwatch_client, instance_id)
            rule_name = create_cloudwatch_event_rule(events_client, instance_id, alarm_name)

            return {
                'statusCode': 200,
                'body': json.dumps('CloudWatch Alarm and EventBridge Rule successfully created for Instance')
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    


    
