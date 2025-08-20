"""
Prompt templates for the Deep Research Production System.
Centralized prompt management for consistent and maintainable prompts.
"""

from typing import Dict, Any


class PromptTemplates:
    """Centralized prompt templates for the research system."""
    
    # Planning and Query Generation
    PLANNING_QUERY_GENERATOR = """
    You're an AI research assistant.
    Based on the topic: "{topic}", generate 5-7 focused research questions 
    that should be answered to plan a comprehensive report.
    Return them as a simple numbered list.
    """
    
    REPORT_OUTLINE_GENERATOR = """
    You are a strategic research planner.
    Use the topic: "{topic}"
    Use the following search results to generate a markdown list of 4–6 key report sections.
    Each section should include:
    - Name
    - Description
    - Research: true/false (whether it needs further web research)
    - Content: (leave blank)

    For example:
       - **Name:** NVIDIA's Key Competitive Advantages:
       - **Description:**  Detailed examination of NVIDIA's strategic moves that contribute to its market leadership. This includes technological advancements (CUDA, software ecosystem like TensorRT, RAPIDS, etc.), strategic acquisitions, strong partnerships (e.g., Microsoft), and its first-mover advantage in the AI hardware space.  Analyze the "AI factory" concept and its impact.
       - **Research:** True (requires deeper dive into NVIDIA's technological specifications, partnership agreements, acquisition details, and analysis of the success/impact of the "AI factory" concept)
       - **Content:** [blank]

    Search Results:
    ---
    {search_summary}
    ---
    """
    
    SECTION_QUERY_GENERATOR = """
    You're a research assistant tasked with helping generate research questions.
    Generate 5-7 useful and diverse research questions to explore the section topic: "{section_topic}"
    Return them as a simple numbered list.
    """
    
    # Content Generation
    SECTION_WRITER = """
    You are an expert report writer. Your task is to write a detailed section for a research report.
    Section Title: {section_title}
    Section Description: {section_description}
    Search Documents:
    {documents}

    Instructions:
    - Use a professional and analytical tone.
    - The section should be ~300-400 words.
    - Organize it into 2-3 paragraphs.
    - Use the documents as supporting material.
    - Where appropriate, cite the URLs in parentheses.

    Now write the content of this section:
    """
    
    INTRODUCTION_WRITER = """
    You are an expert research summarizer. Use a professional, analytical, and engaging tone.
    Write the introduction for a research report titled: "{topic}"

    Content Summary:
    {section_texts}

    Guidelines:
    - Length: ~150–200 words
    - Introduction should preview what will be covered and why it's relevant.
    - Do not repeat full section titles or cite specific URLs.
    """
    
    CONCLUSION_WRITER = """
    You are an expert research summarizer. Use a professional, analytical, and engaging tone.
    Write the conclusion for a research report titled: "{topic}"

    Content Summary:
    {section_texts}

    Guidelines:
    - Length: ~150–200 words
    - Conclusion should summarize the key takeaways and offer closing insights.
    - Do not repeat full section titles or cite specific URLs.
    """
    
    # Validation Prompts
    GROUNDING_VALIDATION = """
    Analyze the following content for factual grounding in the provided sources.
    
    Content to validate:
    {content}
    
    Source documents:
    {sources}
    
    Evaluate:
    1. Are claims in the content supported by the sources?
    2. Are there any unsupported or potentially false claims?
    3. Is the content accurately representing the source information?
    
    Provide a score from 0-1 and list any hallucinated claims.
    """
    
    COVERAGE_VALIDATION = """
    Evaluate how well the content covers the intended queries.
    
    Content:
    {content}
    
    Intended queries:
    {queries}
    
    Assess:
    1. Does the content address all the queries?
    2. Are there any gaps in coverage?
    3. Is the depth of coverage appropriate?
    
    Provide a score from 0-1 and list any coverage gaps.
    """
    
    READABILITY_VALIDATION = """
    Assess the readability and quality of the content.
    
    Content:
    {content}
    
    Evaluate:
    1. Is the writing clear and coherent?
    2. Is the grammar and structure correct?
    3. Is the tone appropriate for the audience?
    4. Is the content well-organized?
    
    Provide a score from 0-1 and list any issues.
    """
    
    # Error Handling
    ERROR_RETRY_PROMPT = """
    The previous attempt to generate content failed. Please try again with a simpler approach.
    
    Original request: {original_request}
    Error: {error_message}
    
    Please provide a response that addresses the original request but with a more straightforward approach.
    """
    
    # Quality Assessment
    QUALITY_ASSESSMENT = """
    Assess the overall quality of this research report.
    
    Report Title: {topic}
    Report Content:
    {content}
    
    Evaluate the following aspects:
    1. Completeness: Does it cover all important aspects of the topic?
    2. Accuracy: Are the facts and claims well-supported?
    3. Clarity: Is the writing clear and easy to understand?
    4. Structure: Is the report well-organized?
    5. Depth: Does it provide sufficient detail and analysis?
    
    Provide a score from 0-1 for each aspect and an overall quality score.
    """
    
    @classmethod
    def format_prompt(cls, template_name: str, **kwargs) -> str:
        """
        Format a prompt template with provided parameters.
        
        Args:
            template_name: Name of the template to use
            **kwargs: Parameters to format the template with
            
        Returns:
            Formatted prompt string
        """
        template = getattr(cls, template_name, None)
        if template is None:
            raise ValueError(f"Template '{template_name}' not found")
        
        return template.format(**kwargs)
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, str]:
        """Get all available prompt templates."""
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if name.isupper() and isinstance(getattr(cls, name), str)
        }


# Global prompt templates instance
prompt_templates = PromptTemplates() 