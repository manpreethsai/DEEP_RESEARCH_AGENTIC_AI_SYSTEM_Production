"""
State management models for the Deep Research Agent System.
Defines data structures for tracking agent state and report generation progress.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class AgentState:
    """Main agent state for tracking research and report generation."""
    
    # Core topic and metadata
    topic: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "initialized"
    
    # Planning phase
    plan_queries: List[str] = field(default_factory=list)
    report_outline: Optional[str] = None
    section_titles: List[str] = field(default_factory=list)
    
    # Research phase
    section_queries: Dict[str, List[str]] = field(default_factory=dict)
    section_research: Dict[str, List[str]] = field(default_factory=dict)
    
    # Content generation phase
    section_drafts: Dict[str, str] = field(default_factory=dict)
    formatted_body: Optional[str] = None
    
    # Final compilation
    intro: Optional[str] = None
    conclusion: Optional[str] = None
    compiled_report: Optional[str] = None
    
    # Metadata and tracking
    total_characters: int = 0
    processing_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            'topic': self.topic,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'plan_queries': self.plan_queries,
            'report_outline': self.report_outline,
            'section_titles': self.section_titles,
            'section_queries': self.section_queries,
            'section_research': self.section_research,
            'section_drafts': self.section_drafts,
            'formatted_body': self.formatted_body,
            'intro': self.intro,
            'conclusion': self.conclusion,
            'compiled_report': self.compiled_report,
            'total_characters': self.total_characters,
            'processing_time': self.processing_time,
            'error_messages': self.error_messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create state from dictionary."""
        return cls(
            topic=data['topic'],
            created_at=datetime.fromisoformat(data['created_at']),
            status=data['status'],
            plan_queries=data.get('plan_queries', []),
            report_outline=data.get('report_outline'),
            section_titles=data.get('section_titles', []),
            section_queries=data.get('section_queries', {}),
            section_research=data.get('section_research', {}),
            section_drafts=data.get('section_drafts', {}),
            formatted_body=data.get('formatted_body'),
            intro=data.get('intro'),
            conclusion=data.get('conclusion'),
            compiled_report=data.get('compiled_report'),
            total_characters=data.get('total_characters', 0),
            processing_time=data.get('processing_time', 0.0),
            error_messages=data.get('error_messages', [])
        )
    
    def save(self, filepath: str):
        """Save state to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'AgentState':
        """Load state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class SearchResult:
    """Individual search result from web search."""
    title: str
    content: str
    url: str
    source: str = "tavily"
    relevance_score: Optional[float] = None
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        return f"**{self.title}**\n{self.content}\n({self.url})"


@dataclass
class SectionData:
    """Data structure for a report section."""
    title: str
    description: str
    queries: List[str] = field(default_factory=list)
    research_results: List[SearchResult] = field(default_factory=list)
    content: Optional[str] = None
    word_count: int = 0
    needs_research: bool = True
    
    def add_research_result(self, result: SearchResult):
        """Add a research result to this section."""
        self.research_results.append(result)
    
    def get_research_text(self) -> str:
        """Get all research results as formatted text."""
        return "\n\n".join([result.to_markdown() for result in self.research_results])


@dataclass
class ReportMetrics:
    """Metrics for tracking report quality and performance."""
    total_sections: int = 0
    total_words: int = 0
    total_characters: int = 0
    processing_time: float = 0.0
    api_calls: int = 0
    search_queries: int = 0
    errors: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_sections': self.total_sections,
            'total_words': self.total_words,
            'total_characters': self.total_characters,
            'processing_time': self.processing_time,
            'api_calls': self.api_calls,
            'search_queries': self.search_queries,
            'errors': self.errors,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses
        }


@dataclass
class ValidationResult:
    """Result from content validation."""
    section_title: str
    grounding_score: float
    coverage_score: float
    readability_score: float
    hallucinated_claims: List[str] = field(default_factory=list)
    coverage_gaps: List[str] = field(default_factory=list)
    readability_issues: List[str] = field(default_factory=list)
    overall_score: float = 0.0
    
    def calculate_overall_score(self) -> float:
        """Calculate overall validation score."""
        self.overall_score = (
            self.grounding_score * 0.4 +
            self.coverage_score * 0.4 +
            self.readability_score * 0.2
        )
        return self.overall_score 