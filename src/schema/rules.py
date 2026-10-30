"""
rules.py - Pydantic schema for structured eligibility rules, provenance, and user profile (Slice 2).
"""

from enum import Enum
from typing import List, Optional, Union, Literal, Dict, Any
from pydantic import BaseModel, Field

class ReviewStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    VERIFIED = "verified"
    REJECTED = "rejected"

class AttributeName(str, Enum):
    # Core chatbot profile attributes
    AGE = "age"
    ANNUAL_INCOME_INR = "annual_income_inr"
    GENDER = "gender"
    MARITAL_STATUS = "marital_status"
    NUMBER_OF_CHILDREN = "number_of_children"
    STATE_RESIDENCE = "state_residence"
    DISTRICT_RESIDENCE = "district_residence"
    
    # Secondary / specialized scheme attributes
    IS_PREGNANT = "is_pregnant"
    IS_LACTATING = "is_lactating"
    IS_STUDENT = "is_student"
    IS_BPL = "is_bpl"
    SOCIAL_CATEGORY = "social_category"          # SC, ST, OBC, General
    DISABILITY = "disability"                    # bool or specific conditions
    OCCUPATION_CATEGORY = "occupation_category"  # construction_worker, govt_employee, unorganized, etc.
    REGISTERED_WORKER = "registered_worker"      # bool (e.g. BOCW registered)
    RESIDENCE_AREA = "residence_area"            # rural, urban
    SPECIFIC_DIAGNOSIS = "specific_diagnosis"    # hemoglobinopathy, etc.

class Operator(str, Enum):
    EQ = "eq"              # Equal to
    NEQ = "neq"            # Not equal to
    GTE = "gte"            # Greater than or equal to
    LTE = "lte"            # Less than or equal to
    IN = "in"              # Value in set
    CONTAINS = "contains"  # String or collection contains

class LogicalGroupOperator(str, Enum):
    ALL = "ALL"
    ANY = "ANY"
    NOT = "NOT"

class SingleCriterion(BaseModel):
    """Atomic eligibility condition backed by a source sentence."""
    criterion_id: str = Field(description="Unique identifier for criterion")
    attribute: AttributeName
    operator: Operator
    target_value: Union[str, int, float, bool, List[str], List[int]]
    
    # Provenance fields (Hard Rule)
    verbatim_source_sentence: str = Field(
        description="Exact sentence from scheme documentation from which this criterion was derived"
    )
    is_mandatory: bool = Field(
        default=True,
        description="Whether this criterion is strictly mandatory (failing it eliminates eligibility)"
    )
    review_status: ReviewStatus = Field(
        default=ReviewStatus.UNREVIEWED,
        description="Human review status: unreviewed, verified, or rejected"
    )
    reviewer_note: Optional[str] = Field(
        default="",
        description="Notes from domain expert or researcher during review"
    )

class CriterionGroup(BaseModel):
    """Boolean combination of criteria (ALL, ANY, or NOT)."""
    operator: LogicalGroupOperator
    criteria: List[Union[SingleCriterion, "CriterionGroup"]]
    group_description: Optional[str] = None

# Support nested recursive definition
CriterionGroup.model_rebuild()

class SchemeEligibilityRule(BaseModel):
    """Top-level structured eligibility rule for a scheme."""
    scheme_id: str
    rule_group: CriterionGroup
    unmodeled_discretionary_conditions: Optional[str] = Field(
        default="",
        description="Conditions that cannot be evaluated deterministically (e.g., 'officer discretion')"
    )

class UserProfile(BaseModel):
    """User profile. All fields optional to explicitly model unknown/missing data."""
    age: Optional[int] = None
    annual_income_inr: Optional[float] = None
    gender: Optional[str] = None                    # female, male, other
    marital_status: Optional[str] = None            # unmarried, married, widowed, divorced, deserted
    number_of_children: Optional[int] = None
    state_residence: Optional[str] = None
    district_residence: Optional[str] = None
    
    # Secondary attributes
    is_pregnant: Optional[bool] = None
    is_lactating: Optional[bool] = None
    is_student: Optional[bool] = None
    is_bpl: Optional[bool] = None
    social_category: Optional[str] = None           # SC, ST, OBC, General
    disability: Optional[bool] = None
    occupation_category: Optional[str] = None       # construction_worker, govt_employee, etc.
    registered_worker: Optional[bool] = None
    residence_area: Optional[str] = None            # rural, urban
    specific_diagnosis: Optional[List[str]] = None

