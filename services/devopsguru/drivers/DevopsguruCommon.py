import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class DevopsguruCommon(Evaluator):
    def __init__(self, resource, devopsguruClient):
        super().__init__()
        self.init()
        self.resource = resource
        self.devopsguruClient = devopsguruClient
        self._resourceName = 'Account'
        
    def _checkDevOpsGuruEnabled(self):
        try:
            response = self.devopsguruClient.describe_service_integration()
            service_integration = response.get('ServiceIntegration', {})
            
            # Check if DevOps Guru is enabled
            if not service_integration:
                self.results['DevOpsGuruEnabled'] = [-1, "DevOps Guru is not enabled"]
                return
                
            # Check OpsCenterIntegration
            ops_center = service_integration.get('OpsCenterIntegration', {})
            if ops_center.get('OptInStatus') != 'ENABLED':
                self.results['OpsCenterIntegration'] = [-1, "OpsCenter integration is not enabled"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                self.results['DevOpsGuruEnabled'] = [-1, "DevOps Guru is not enabled or access denied"]
            else:
                self.results['DevOpsGuruEnabled'] = [-1, f"Unable to check DevOps Guru status: {str(e)}"]
    
    def _checkResourceCollection(self):
        try:
            response = self.devopsguruClient.get_resource_collection(
                ResourceCollectionType='AWS_CLOUD_FORMATION'
            )
            
            cf_stacks = response.get('ResourceCollection', {}).get('CloudFormation', {}).get('StackNames', [])
            if not cf_stacks:
                self.results['ResourceCollection'] = [-1, "No CloudFormation stacks configured for monitoring"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException', 'ResourceNotFoundException']:
                self.results['ResourceCollection'] = [-1, f"Unable to check resource collection: {str(e)}"]
    
    def _checkInsights(self):
        try:
            response = self.devopsguruClient.list_insights(
                StatusFilter={'Any': {'Type': 'REACTIVE', 'StartTimeRange': {}}}
            )
            
            insights = response.get('ReactiveInsights', [])
            if insights:
                open_insights = [i for i in insights if i.get('Status') == 'ONGOING']
                if open_insights:
                    self.results['OpenInsights'] = [-1, f"{len(open_insights)} open insights require attention"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['InsightsCheck'] = [-1, f"Unable to check insights: {str(e)}"]