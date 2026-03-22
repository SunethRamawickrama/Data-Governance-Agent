from dataclasses import dataclass
from abc import abstractmethod, ABC
from enum import Enum
import datetime
from typing import Optional

class SourceType(str, Enum):
    DATABASE = "database"
    FILE     = "file"
    S3       = "s3"
 
class Classification(str, Enum):
    PII       = "PII"
    QUASI_PII = "QUASI_PII"
    SAFE      = "SAFE"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"

class RemediationType(str, Enum):
    REDACT                  = "REDACT"
    ENCRYPT                 = "ENCRYPT"
    RESTRICT                = "RESTRICT"
    FIX_RETENTION_POLICY    = "FIX_RETENTION_POLICY"
    DOCUMENT_CONSENT_BASIS  = "DOCUMENT_CONSENT_BASIS"
    FIX_ACCESS_CONTROL      = "FIX_ACCESS_CONTROL"

'''these types represent details/structure/data about a given database/file system/bucket'''

@dataclass
class ColumnReport:
    '''information and sample data for a given column or single sub part within a document
    Ex: column in a table within a db, sub-section of a file in a file system'''
    column_name:    str
    data_type:      str                 # what typa data it contains
    sample_values:  list                # up to 5 representative values
 
@dataclass
class TableReport:
    '''information for an entire table or a file'''
    table_name:  str                    # for files: filename, for buckets: key/url
    row_count:   int
    columns:     list[ColumnReport]
    sample_rows: list[dict]             # up to 5 full rows
    metadata:    dict                   # retention_policy, owner, access_control, and other important data
 
@dataclass
class SourceScanReport:
    '''information of the entire db, system, source'''
    source_id:   str
    source_name: str
    source_type: str
    scanned_at:  datetime
    tables:      list[TableReport]

'''These types relate to PII data and their classifications'''

@dataclass
class ClassifiedColumn:
    '''classification for single column/entity'''
    column_name:    str
    classification: Classification      # either PII/Quasi PII/safe with raw data
    justification:  str                 # LLM reasoning with policy citation
    policy_refs:    list[str]           # referred documents from the knowledge base

@dataclass
class ClassifiedTable:
    '''classification for an entire table/file/bucket. Named as table for db usage, but compatible with files and buckets'''
    table_name:        str                          # name of the source
    classified_columns: list[ClassifiedColumn]      # classification details for all the cols/entities
    metadata:          dict
    pii_count:         int
    quasi_pii_count:   int
    safe_count:        int

@dataclass
class ClassifiedReport:
    '''classification report for the entire source such as the database, file system'''
    source_id:  str
    frameworks: list[str]               # frameworks we are audit against. Ex: internal data policies, state regulations, etc.
    tables:     list[ClassifiedTable]   # distinct report for all the tables etc.
    classified_at: datetime

'''These types contain any policy violations found within the classification report.
examples include unencrypted PII data, security violations from raw data and 
violations found within metadata such as datasets without owners, retention policy violations etc'''
@dataclass
class Violation:
    violation_id:      str
    severity:          Severity
    rule:              str         # exact citation found for policy violation  
    affected_columns:  list[str]
    table_name:        str
    framework:         str

@dataclass
class ViolationReport:
    source_id:       str
    violations:      list[Violation]
    critical_count:  int
    high_count:      int
    medium_count:    int
    checked_at:      datetime

'''These types include what remeditions should be taken to fix each violation.
The data is recieved from the policy data stored in the vector store or LLM suggestions based on violated policy'''
@dataclass
class Remediation:
    violation_id:      str
    remediation_type:  RemediationType
    affected_columns:  list[str]
    table_name:        str
    policy_basis:      str             # what policy is violated and why it should be fixed
    recommended_solution: str          # recommended solution. The agent will check if the solution could be applied through given mcp capabilities

@dataclass
class RemediationReport:
    source_id:     str
    remediations:  list[Remediation]
    generated_at:  datetime

'''These types will contain all the info for an audit report'''

@dataclass
class AuditReport:
    audit_id:           str
    source_id:          str
    source_name:        str
    source_type:        str
    frameworks:         list[str]
    scan_report:        SourceScanReport
    classified_report:  ClassifiedReport
    violation_report:   ViolationReport
    remediation_report: RemediationReport
    started_at:         datetime
    completed_at:       datetime
    summary:            str


'''Structure of the audit job'''
@dataclass
class AuditJob:
    job_id:      str
    source_id:   str
    source_name: str
    source_type: str 
    frameworks:  list[str]
    created_at:  datetime

@dataclass
class DataSource:
    name: str
    type: SourceType

'''Shared state graph of the audit workflow. This is a deterministic worklow that operates in steps rather than 
the orchestrator agent dynamically deciding next steps. This is implemented in a sequence to depict both dynamic
decision making and workflows where the route is pre-defined. This helps in debugging and understanding where a 
failure would occur in a workflow.'''
@dataclass
class AuditWorkflow:
    job:                AuditJob
    source:             Optional[DataSource]        = None  # filled by SourceResolutionNode
    scan_report:        Optional[SourceScanReport]  = None  # filled by DiscoveryNode
    classified_report:  Optional[ClassifiedReport]  = None  # filled by ClassificationNode
    violation_report:   Optional[ViolationReport]   = None  # filled by PolicyNode
    remediation_report: Optional[RemediationReport] = None  # filled by RemediationNode
    audit_report:       Optional[AuditReport]       = None  # filled by ReportAssemblyNode
    failed_at_node:     Optional[str]               = None
    error:              Optional[str]

'''This is the blueprint for all the nodes in the audit workflow. The run method at each step will execute its 
own overriden run method to update the state using the AI agents'''
class WorkflowNode(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def run(self, state: AuditWorkflow) -> AuditWorkflow:
        pass

'''Exception type to indicate that a node has failed'''
class NodeFailure(Exception):
    def __init__(self, node_name: str, reason: str):
        self.node_name = node_name
        self.reason    = reason
        super().__init__(f"[{node_name}] {reason}")
