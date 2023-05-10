
from .RdsCommon import RdsCommon

class RdsMysql(RdsCommon):
    def __init__(self, db, rdsClient):
        super().__init__(db, rdsClient)
        self.loadParameterInfo()
        
    def _checkEnableLogs(self):
        logsExports = self.db.get('EnabledCloudwatchLogsExports', [])
        
        if 'error' not in logsExports:
            self.results['MYSQL__LogsGeneral'] = [-1, 'ALL']
        elif 'error' not in logsExports:
            self.results['MYSQL__LogsErrorEnable'] = [-1, 'Disabled']
    
    # Todo: 
    # https://aws.amazon.com/blogs/database/best-practices-for-configuring-parameters-for-amazon-rds-for-mysql-part-2-parameters-related-to-replication/
    # https://aws.amazon.com/blogs/database/best-practices-for-configuring-parameters-for-amazon-rds-for-mysql-part-1-parameters-related-to-performance/
    def _checkParamSyncBinLog(self):
        sync_binLog = self.dbParams.get('sync_binlog', False)
        if sync_binLog != 1:
            self.results['MYSQL__param_syncBinLog'] = [-1, 'null' if sync_binLog is False else sync_binLog]
    
    def _checkParamInnoDbFlushTrxCommit(self):
        flushCommit = self.dbParams.get('innodb_flush_log_at_trx_commit', False)
        if flushCommit == 0 or flushCommit == 2:
            self.results['MYSQL__param_innodbFlushTrxCommit'] = [-1, 'null' if flushCommit is False else flushCommit]
    
    def _checkParamPerfSchema(self):
        ps = self.dbParams.get('performance_schema', False)
        if not ps:
            self.results['MYSQL__PerfSchema'] = [-1, ps]
