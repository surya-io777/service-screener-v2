import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class SystemsmanagerCommon(Evaluator):
    def __init__(self, resource, ssmClient):
        super().__init__()
        self.init()
        self.resource = resource
        self.ssmClient = ssmClient
        self._resourceName = 'Account'
        
    def _checkSessionManager(self):
        try:
            response = self.ssmClient.describe_document_permission(
                Name='SSM-SessionManagerRunShell'
            )
            # If document exists, Session Manager is available
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidDocument':
                self.results['SessionManager'] = [-1, "Session Manager is not properly configured"]
    
    def _checkPatchCompliance(self):
        try:
            response = self.ssmClient.describe_instance_patch_states()
            instances = response.get('InstancePatchStates', [])
            
            non_compliant = [i for i in instances if i.get('OperationEndTime') and 
                           i.get('FailedCount', 0) > 0]
            
            if non_compliant:
                self.results['PatchCompliance'] = [-1, f"{len(non_compliant)} instances have patch compliance issues"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['PatchComplianceCheck'] = [-1, f"Unable to check patch compliance: {str(e)}"]
    
    def _checkParameterStore(self):
        try:
            response = self.ssmClient.describe_parameters(MaxResults=10)
            parameters = response.get('Parameters', [])
            
            # Check for insecure parameters
            insecure_params = [p for p in parameters if p.get('Type') == 'String' and 
                             any(keyword in p.get('Name', '').lower() for keyword in 
                                 ['password', 'secret', 'key', 'token'])]
            
            if insecure_params:
                self.results['InsecureParameters'] = [-1, f"{len(insecure_params)} parameters may contain sensitive data without encryption"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['ParameterStoreCheck'] = [-1, f"Unable to check Parameter Store: {str(e)}"]
    
    def _checkManagedInstances(self):
        try:
            response = self.ssmClient.describe_instance_information()
            instances = response.get('InstanceInformationList', [])
            
            if not instances:
                self.results['ManagedInstances'] = [-1, "No instances are managed by Systems Manager"]
            else:
                offline_instances = [i for i in instances if i.get('PingStatus') != 'Online']
                if offline_instances:
                    self.results['OfflineInstances'] = [-1, f"{len(offline_instances)} managed instances are offline"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['ManagedInstancesCheck'] = [-1, f"Unable to check managed instances: {str(e)}"]