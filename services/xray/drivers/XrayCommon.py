import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class XrayCommon(Evaluator):
    def __init__(self, resource, xrayClient):
        super().__init__()
        self.init()
        self.resource = resource
        self.xrayClient = xrayClient
        self._resourceName = 'Account'
        
    def _checkTracingEnabled(self):
        try:
            response = self.xrayClient.get_service_graph()
            services = response.get('Services', [])
            
            if not services:
                self.results['TracingEnabled'] = [-1, "No services are sending traces to X-Ray"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['TracingEnabledCheck'] = [-1, f"Unable to check tracing status: {str(e)}"]
        except Exception as e:
            self.results['TracingEnabledCheck'] = [-1, f"Unable to check tracing status: {str(e)}"]
    
    def _checkEncryptionConfig(self):
        try:
            response = self.xrayClient.get_encryption_config()
            
            encryption_config = response.get('EncryptionConfig', {})
            if encryption_config.get('Type') != 'KMS':
                self.results['EncryptionConfig'] = [-1, "X-Ray traces are not encrypted with KMS"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['EncryptionConfigCheck'] = [-1, f"Unable to check encryption config: {str(e)}"]
        except Exception as e:
            self.results['EncryptionConfigCheck'] = [-1, f"Unable to check encryption config: {str(e)}"]
    
    def _checkSamplingRules(self):
        try:
            response = self.xrayClient.get_sampling_rules()
            
            rules = response.get('SamplingRuleRecords', [])
            if not rules:
                self.results['SamplingRules'] = [-1, "No custom sampling rules configured"]
            else:
                # Check for overly permissive rules
                high_rate_rules = [r for r in rules if r.get('SamplingRule', {}).get('FixedRate', 0) > 0.5]
                if high_rate_rules:
                    self.results['HighSamplingRate'] = [-1, f"{len(high_rate_rules)} sampling rules have high sampling rates (>50%)"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['SamplingRulesCheck'] = [-1, f"Unable to check sampling rules: {str(e)}"]
        except Exception as e:
            self.results['SamplingRulesCheck'] = [-1, f"Unable to check sampling rules: {str(e)}"]
    
    def _checkInsightsEnabled(self):
        try:
            response = self.xrayClient.get_insight_summaries()
            
            # If we can get insights, the feature is enabled
            insights = response.get('InsightSummaries', [])
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidRequestException':
                self.results['InsightsEnabled'] = [-1, "X-Ray Insights is not enabled"]
            elif e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['InsightsEnabledCheck'] = [-1, f"Unable to check insights status: {str(e)}"]
        except Exception as e:
            self.results['InsightsEnabledCheck'] = [-1, f"Unable to check insights status: {str(e)}"]