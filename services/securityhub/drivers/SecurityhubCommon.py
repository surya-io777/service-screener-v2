import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class SecurityhubCommon(Evaluator):
    def __init__(self, resource, securityhubClient):
        super().__init__()
        self.init()
        self.resource = resource
        self.securityhubClient = securityhubClient
        self._resourceName = 'Account'
        
    def _checkSecurityHubEnabled(self):
        try:
            response = self.securityhubClient.describe_hub()
            
            # Check if Security Hub is enabled
            if not response:
                self.results['SecurityHubEnabled'] = [-1, "Security Hub is not enabled"]
                return
                
            # Check auto-enable controls
            auto_enable_controls = response.get('AutoEnableControls')
            if not auto_enable_controls:
                self.results['AutoEnableControls'] = [-1, "Auto-enable controls is not configured"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidAccessException':
                self.results['SecurityHubEnabled'] = [-1, "Security Hub is not enabled"]
            else:
                self.results['SecurityHubEnabled'] = [-1, f"Unable to check Security Hub status: {str(e)}"]
    
    def _checkStandards(self):
        try:
            response = self.securityhubClient.get_enabled_standards()
            
            standards = response.get('StandardsSubscriptions', [])
            if not standards:
                self.results['SecurityStandards'] = [-1, "No security standards are enabled"]
                return
                
            # Check for common standards
            standard_arns = [s.get('StandardsArn', '') for s in standards]
            
            aws_foundational = any('aws-foundational-security' in arn for arn in standard_arns)
            cis = any('cis-aws-foundations-benchmark' in arn for arn in standard_arns)
            pci_dss = any('pci-dss' in arn for arn in standard_arns)
            
            if not aws_foundational:
                self.results['AWSFoundationalStandard'] = [-1, "AWS Foundational Security Standard is not enabled"]
            if not cis:
                self.results['CISStandard'] = [-1, "CIS AWS Foundations Benchmark is not enabled"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['InvalidAccessException']:
                self.results['StandardsCheck'] = [-1, f"Unable to check standards: {str(e)}"]
    
    def _checkFindings(self):
        try:
            response = self.securityhubClient.get_findings(
                Filters={
                    'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
                    'WorkflowStatus': [{'Value': 'NEW', 'Comparison': 'EQUALS'}]
                },
                MaxResults=50
            )
            
            findings = response.get('Findings', [])
            if findings:
                critical_findings = [f for f in findings if f.get('Severity', {}).get('Label') == 'CRITICAL']
                high_findings = [f for f in findings if f.get('Severity', {}).get('Label') == 'HIGH']
                
                if critical_findings:
                    self.results['CriticalFindings'] = [-1, f"{len(critical_findings)} critical findings require immediate attention"]
                elif high_findings:
                    self.results['HighFindings'] = [-1, f"{len(high_findings)} high severity findings require attention"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['InvalidAccessException']:
                self.results['FindingsCheck'] = [-1, f"Unable to check findings: {str(e)}"]