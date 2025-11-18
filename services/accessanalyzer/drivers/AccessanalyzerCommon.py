import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class AccessanalyzerCommon(Evaluator):
    def __init__(self, analyzer, accessanalyzerClient):
        super().__init__()
        self.init()
        self.analyzer = analyzer
        self.accessanalyzerClient = accessanalyzerClient
        self._resourceName = analyzer.get('name', 'Account')
        
    def _checkAccessAnalyzerEnabled(self):
        if not self.analyzer:
            self.results['AccessAnalyzerEnabled'] = [-1, "Access Analyzer is not enabled"]
            return
        
        # Check analyzer status
        if self.analyzer.get('status') != 'ACTIVE':
            self.results['AnalyzerStatus'] = [-1, f"Analyzer {self.analyzer['name']} is not active"]
    
    def _checkFindings(self):
        if not self.analyzer:
            return
            
        try:
            response = self.accessanalyzerClient.list_findings(
                analyzerArn=self.analyzer['arn'],
                filter={'status': {'eq': ['ACTIVE']}}
            )
            
            findings = response.get('findings', [])
            if findings:
                critical_findings = [f for f in findings if f.get('condition', {}).get('public') == True]
                if critical_findings:
                    self.results['PublicFindings'] = [-1, f"{len(critical_findings)} resources are publicly accessible"]
                elif findings:
                    self.results['AccessFindings'] = [-1, f"{len(findings)} access findings require review"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['FindingsCheck'] = [-1, f"Unable to check findings: {str(e)}"]
    
    def _checkAnalyzerType(self):
        if not self.analyzer:
            return
            
        analyzer_type = self.analyzer.get('type')
        if analyzer_type == 'ACCOUNT':
            # Account analyzer only analyzes resources within the account
            pass
        elif analyzer_type == 'ORGANIZATION':
            # Organization analyzer can analyze resources across the organization
            pass
        else:
            self.results['AnalyzerType'] = [-1, f"Unknown analyzer type: {analyzer_type}"]