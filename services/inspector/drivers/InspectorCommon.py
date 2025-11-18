import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class InspectorCommon(Evaluator):
    def __init__(self, resource, inspectorClient, accountId):
        super().__init__()
        self.init()
        self.resource = resource
        self.inspectorClient = inspectorClient
        self.accountId = accountId
        self._resourceName = 'Account'
        
    def _checkInspectorEnabled(self):
        try:
            response = self.inspectorClient.batch_get_account_status(
                accountIds=[self.accountId]
            )
            
            accounts = response.get('accounts', [])
            if not accounts:
                self.results['InspectorEnabled'] = [-1, "Inspector is not enabled"]
                return
                
            account = accounts[0]
            resource_state = account.get('resourceState', {})
            
            # Check EC2 scanning
            ec2_state = resource_state.get('ec2', {})
            if ec2_state.get('status') != 'ENABLED':
                self.results['EC2Scanning'] = [-1, "Inspector EC2 scanning is not enabled"]
                
            # Check ECR scanning
            ecr_state = resource_state.get('ecr', {})
            if ecr_state.get('status') != 'ENABLED':
                self.results['ECRScanning'] = [-1, "Inspector ECR scanning is not enabled"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                self.results['InspectorEnabled'] = [-1, "Inspector is not enabled or access denied"]
            else:
                self.results['InspectorEnabled'] = [-1, f"Unable to check Inspector status: {str(e)}"]
    
    def _checkFindings(self):
        try:
            response = self.inspectorClient.list_findings(
                filterCriteria={
                    'findingStatus': [{'comparison': 'EQUALS', 'value': 'ACTIVE'}]
                },
                maxResults=50
            )
            
            findings = response.get('findings', [])
            if findings:
                critical_findings = [f for f in findings if f.get('severity') == 'CRITICAL']
                high_findings = [f for f in findings if f.get('severity') == 'HIGH']
                
                if critical_findings:
                    self.results['CriticalFindings'] = [-1, f"{len(critical_findings)} critical security findings require immediate attention"]
                elif high_findings:
                    self.results['HighFindings'] = [-1, f"{len(high_findings)} high severity findings require attention"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['FindingsCheck'] = [-1, f"Unable to check findings: {str(e)}"]
    
    def _checkCoverageStats(self):
        try:
            response = self.inspectorClient.get_coverage_statistics(
                filterCriteria={}
            )
            
            counts = response.get('countsByResourceType', {})
            total_resources = sum(counts.values()) if counts else 0
            
            if total_resources == 0:
                self.results['CoverageStats'] = [-1, "No resources are being scanned by Inspector"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['CoverageStats'] = [-1, f"Unable to check coverage statistics: {str(e)}"]