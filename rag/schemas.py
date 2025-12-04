from pydantic import BaseModel, Field
from typing import List, Optional

class CVSummarySchema(BaseModel):
    name: Optional[str] = Field(None, description="Candidate name if available")
    current_title: Optional[str] = Field(None, description="Current job title")
    years_experience: Optional[float] = Field(None, description="Total years of experience (integer)")
    skills: Optional[List[str]] = Field(default_factory=list, description="List of candidate's skills")
    work_history: Optional[List[str]] = Field(default_factory=list, description="List of candidate's work history")
    education: Optional[List[str]] = Field(default_factory=list, description="List of candidate's education")
    certifications: Optional[List[str]] = Field(default_factory=list, description="List of candidate's certifications")
