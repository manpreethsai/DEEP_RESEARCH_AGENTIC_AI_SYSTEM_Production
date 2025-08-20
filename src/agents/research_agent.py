"""
Research Agent for the Deep Research Production System.
Main orchestrator for research and report generation workflow.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from ..models.state import AgentState, ReportMetrics
from ..core.llm_service import llm_service
from ..core.search_service import search_service
from ..utils.monitoring import PerformanceMonitor, metrics_collector
from ..utils.validation import content_validator
from ..config.settings import config

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Main research agent for orchestrating the research and report generation process."""
    
    def __init__(self):
        """Initialize research agent."""
        self.config = config
        self.metrics = metrics_collector
        
        logger.info("Research Agent initialized")
    
    def create_agent_state(self, topic: str) -> AgentState:
        """
        Create initial agent state for a research topic.
        
        Args:
            topic: Research topic
            
        Returns:
            Initialized agent state
        """
        logger.info(f"Creating agent state for topic: {topic}")
        
        state = AgentState(topic=topic)
        state.status = "initialized"
        
        return state
    
    def generate_planning_queries(self, state: AgentState) -> AgentState:
        """
        Generate initial planning queries for the research topic.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with planning queries
        """
        with PerformanceMonitor("generate_planning_queries", self.metrics):
            logger.info(f"Generating planning queries for topic: {state.topic}")
            
            prompt = f"""
            You're an AI research assistant.
            Based on the topic: "{state.topic}", generate 5-7 focused research questions 
            that should be answered to plan a comprehensive report.
            Return them as a simple numbered list.
            """
            
            try:
                response = llm_service.generate_content(prompt)
                
                # Parse the numbered list into individual queries
                queries = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-')):
                        # Remove numbering and clean up
                        query = line.lstrip('0123456789.- ').strip()
                        if query:
                            queries.append(query)
                
                state.plan_queries = queries
                state.status = "planning_queries_generated"
                
                logger.info(f"Generated {len(queries)} planning queries")
                
            except Exception as e:
                logger.error(f"Failed to generate planning queries: {e}")
                state.error_messages.append(f"Planning query generation failed: {str(e)}")
                state.plan_queries = []
        
        return state
    
    def generate_report_outline(self, state: AgentState) -> AgentState:
        """
        Generate report outline based on planning queries and search results.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with report outline
        """
        with PerformanceMonitor("generate_report_outline", self.metrics):
            logger.info(f"Generating report outline using {len(state.plan_queries)} planning queries")
            
            try:
                # Collect search results from all planning queries
                all_results = []
                for i, query in enumerate(state.plan_queries, 1):
                    logger.info(f"  Searching query {i}/{len(state.plan_queries)}: '{query[:40]}...'")
                    
                    search_results = search_service.search(query)
                    formatted_results = [result.to_markdown() for result in search_results]
                    all_results.extend(formatted_results)
                
                search_summary = "\n\n".join(all_results)
                logger.info(f"  Collected {len(all_results)} total search results")
                
                # Generate report outline
                prompt = f"""
                You are a strategic research planner.
                Use the topic: "{state.topic}"
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
                
                outline = llm_service.generate_content(prompt)
                state.report_outline = outline
                
                # Extract section titles from markdown list
                section_names = []
                for line in outline.splitlines():
                    if line.strip().startswith("- **Name:** "):
                        section_name = line.split(":", 1)[1].strip()
                        section_names.append(section_name)
                
                state.section_titles = section_names
                state.status = "outline_generated"
                
                logger.info(f"Generated report outline with {len(section_names)} sections")
                
            except Exception as e:
                logger.error(f"Failed to generate report outline: {e}")
                state.error_messages.append(f"Report outline generation failed: {str(e)}")
                state.report_outline = "Unable to generate outline at this time."
                state.section_titles = []
        
        return state
    
    def generate_section_queries(self, state: AgentState) -> AgentState:
        """
        Generate section-specific research queries for each section.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with section queries
        """
        with PerformanceMonitor("generate_section_queries", self.metrics):
            logger.info(f"Generating section-specific queries for {len(state.section_titles)} sections")
            
            try:
                for i, section in enumerate(state.section_titles, 1):
                    logger.info(f"  Generating queries for section {i}/{len(state.section_titles)}: '{section}'")
                    
                    prompt = f"""
                    You're a research assistant tasked with helping generate research questions.
                    Generate 5-7 useful and diverse research questions to explore the section topic: "{section}"
                    Return them as a simple numbered list.
                    """
                    
                    raw_questions = llm_service.generate_content(prompt)
                    
                    # Parse the numbered list into individual queries
                    queries = []
                    for line in raw_questions.split('\n'):
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith('-')):
                            query = line.lstrip('0123456789.- ').strip()
                            if query:
                                queries.append(query)
                    
                    state.section_queries[section] = queries
                    logger.info(f"    Generated {len(queries)} queries for section '{section}'")
                
                total_queries = sum(len(queries) for queries in state.section_queries.values())
                logger.info(f"Generated {total_queries} total section-specific queries")
                state.status = "section_queries_generated"
                
            except Exception as e:
                logger.error(f"Failed to generate section queries: {e}")
                state.error_messages.append(f"Section query generation failed: {str(e)}")
                state.section_queries = {}
        
        return state
    
    def perform_section_research(self, state: AgentState) -> AgentState:
        """
        Perform web research for each section using generated queries.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with research results
        """
        with PerformanceMonitor("perform_section_research", self.metrics):
            logger.info(f"Performing web searches for {len(state.section_queries)} sections")
            
            try:
                for section, queries in state.section_queries.items():
                    logger.info(f"  Searching for section: '{section}' ({len(queries)} queries)")
                    
                    research_docs = []
                    for j, query in enumerate(queries, 1):
                        logger.info(f"    Searching query {j}/{len(queries)}: '{query[:40]}...'")
                        
                        search_results = search_service.search(query)
                        formatted_results = [result.to_markdown() for result in search_results]
                        research_docs.extend(formatted_results)
                    
                    state.section_research[section] = research_docs
                    logger.info(f"    Collected {len(research_docs)} results for section '{section}'")
                
                total_results = sum(len(results) for results in state.section_research.values())
                logger.info(f"Completed web searches - collected {total_results} total results")
                state.status = "research_completed"
                
            except Exception as e:
                logger.error(f"Failed to complete web searches: {e}")
                state.error_messages.append(f"Web research failed: {str(e)}")
                state.section_research = {}
        
        return state
    
    def write_section_drafts(self, state: AgentState) -> AgentState:
        """
        Write draft content for each section using research results.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with section drafts
        """
        with PerformanceMonitor("write_section_drafts", self.metrics):
            logger.info(f"Writing section drafts for {len(state.section_titles)} sections")
            
            if self.config.report.parallel_processing:
                return self._write_sections_parallel(state)
            else:
                return self._write_sections_sequential(state)
    
    def _write_sections_sequential(self, state: AgentState) -> AgentState:
        """Write sections sequentially."""
        try:
            for i, section in enumerate(state.section_titles, 1):
                logger.info(f"  Writing draft for section {i}/{len(state.section_titles)}: '{section}'")
                
                # Extract section description from outline
                description = "Description not available"
                for line in state.report_outline.splitlines():
                    if f"- Name: {section}" in line:
                        idx = state.report_outline.splitlines().index(line)
                        desc_line = state.report_outline.splitlines()[idx + 1]
                        if desc_line.startswith("- Description"):
                            description = desc_line.split(":", 1)[1].strip()
                
                # Get research documents for this section
                documents = "\n\n".join(state.section_research.get(section, []))
                
                # Generate section content
                prompt = f"""
                You are an expert report writer. Your task is to write a detailed section for a research report.
                Section Title: {section}
                Section Description: {description}
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
                
                draft_content = llm_service.generate_content(prompt)
                state.section_drafts[section] = draft_content
                
                logger.info(f"    Generated {len(draft_content)} characters for section '{section}'")
            
            total_content = sum(len(content) for content in state.section_drafts.values())
            logger.info(f"Completed section drafts - generated {total_content} total characters")
            state.status = "drafts_completed"
            
        except Exception as e:
            logger.error(f"Failed to write section drafts: {e}")
            state.error_messages.append(f"Section draft writing failed: {str(e)}")
            state.section_drafts = {}
        
        return state
    
    def _write_sections_parallel(self, state: AgentState) -> AgentState:
        """Write sections in parallel using ThreadPoolExecutor."""
        try:
            def write_section(section):
                """Helper function to write a single section."""
                logger.info(f"    Writing section: '{section}' (parallel)")
                
                # Extract section description from outline
                description = "Description not available"
                for line in state.report_outline.splitlines():
                    if f"- Name: {section}" in line:
                        idx = state.report_outline.splitlines().index(line)
                        desc_line = state.report_outline.splitlines()[idx + 1]
                        if desc_line.startswith("- Description"):
                            description = desc_line.split(":", 1)[1].strip()
                
                # Get research documents for this section
                documents = "\n\n".join(state.section_research.get(section, []))
                
                # Generate section content
                prompt = f"""
                You are an expert report writer. Your task is to write a detailed section for a research report.
                Section Title: {section}
                Section Description: {description}
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
                
                draft_content = llm_service.generate_content(prompt)
                return (section, draft_content)
            
            # Execute section writing in parallel
            with ThreadPoolExecutor(max_workers=self.config.report.max_workers) as executor:
                futures = [executor.submit(write_section, section) for section in state.section_titles]
                
                for future in futures:
                    section, draft = future.result()
                    state.section_drafts[section] = draft
                    logger.info(f"    ✅ Completed section: '{section}' ({len(draft)} characters)")
            
            total_content = sum(len(content) for content in state.section_drafts.values())
            logger.info(f"Completed parallel section writing - generated {total_content} total characters")
            state.status = "drafts_completed"
            
        except Exception as e:
            logger.error(f"Failed to complete parallel section writing: {e}")
            state.error_messages.append(f"Parallel section writing failed: {str(e)}")
            state.section_drafts = {}
        
        return state
    
    def format_sections(self, state: AgentState) -> AgentState:
        """
        Format all section drafts into a single body text.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with formatted body
        """
        with PerformanceMonitor("format_sections", self.metrics):
            logger.info(f"Formatting {len(state.section_titles)} sections into body text")
            
            try:
                formatted = []
                for title in state.section_titles:
                    content = state.section_drafts.get(title, "")
                    formatted.append(f"## {title}\n\n{content}")
                
                state.formatted_body = "\n\n".join(formatted)
                state.status = "sections_formatted"
                
                logger.info(f"Formatted body text - {len(state.formatted_body)} characters")
                
            except Exception as e:
                logger.error(f"Failed to format sections: {e}")
                state.error_messages.append(f"Section formatting failed: {str(e)}")
                state.formatted_body = "Unable to format sections at this time."
        
        return state
    
    def write_final_sections(self, state: AgentState) -> AgentState:
        """
        Write introduction and conclusion sections.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with intro and conclusion
        """
        with PerformanceMonitor("write_final_sections", self.metrics):
            logger.info(f"Writing introduction and conclusion for topic: '{state.topic}'")
            
            try:
                section_texts = state.get("formatted_body", "")
                
                # Generate introduction
                logger.info("  Generating introduction...")
                intro_prompt = f"""
                You are an expert research summarizer. Use a professional, analytical, and engaging tone.
                Write the introduction for a research report titled: "{state.topic}"

                Content Summary:
                {section_texts}

                Guidelines:
                - Length: ~150–200 words
                - Introduction should preview what will be covered and why it's relevant.
                - Do not repeat full section titles or cite specific URLs.
                """
                
                state.intro = llm_service.generate_content(intro_prompt)
                logger.info(f"    Generated introduction: {len(state.intro)} characters")
                
                # Generate conclusion
                logger.info("  Generating conclusion...")
                conclusion_prompt = f"""
                You are an expert research summarizer. Use a professional, analytical, and engaging tone.
                Write the conclusion for a research report titled: "{state.topic}"

                Content Summary:
                {section_texts}

                Guidelines:
                - Length: ~150–200 words
                - Conclusion should summarize the key takeaways and offer closing insights.
                - Do not repeat full section titles or cite specific URLs.
                """
                
                state.conclusion = llm_service.generate_content(conclusion_prompt)
                logger.info(f"    Generated conclusion: {len(state.conclusion)} characters")
                
                state.status = "final_sections_completed"
                logger.info(f"Completed final sections - intro: {len(state.intro)} chars, conclusion: {len(state.conclusion)} chars")
                
            except Exception as e:
                logger.error(f"Failed to write final sections: {e}")
                state.error_messages.append(f"Final section writing failed: {str(e)}")
                state.intro = "Unable to generate introduction at this time."
                state.conclusion = "Unable to generate conclusion at this time."
        
        return state
    
    def compile_final_report(self, state: AgentState) -> AgentState:
        """
        Compile the final report from all sections.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with compiled report
        """
        with PerformanceMonitor("compile_final_report", self.metrics):
            logger.info(f"Compiling final report for topic: '{state.topic}'")
            
            try:
                compiled = [
                    f"# {state.topic}",
                    "\n## Introduction\n" + state.intro,
                    state.formatted_body,
                    "\n## Conclusion\n" + state.conclusion
                ]
                
                state.compiled_report = "\n\n".join(compiled)
                state.total_characters = len(state.compiled_report)
                state.status = "completed"
                
                logger.info(f"Compiled final report - {len(state.compiled_report)} total characters")
                
            except Exception as e:
                logger.error(f"Failed to compile final report: {e}")
                state.error_messages.append(f"Report compilation failed: {str(e)}")
                state.compiled_report = "Unable to compile report at this time."
        
        return state
    
    def run_research_pipeline(self, topic: str, enable_validation: bool = True) -> AgentState:
        """
        Run the complete research and report generation pipeline.
        
        Args:
            topic: Research topic
            enable_validation: Whether to enable content validation
            
        Returns:
            Complete agent state with final report
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting Deep Research and Report Generation Agent")
        logger.info(f"Topic: {topic}")
        logger.info(f"Validation: {'Enabled' if enable_validation else 'Disabled'}")
        logger.info("="*60)
        
        try:
            # Initialize agent state
            state = self.create_agent_state(topic)
            
            # Execute the complete pipeline
            logger.info("\n📋 Step 1: Generating planning queries")
            state = self.generate_planning_queries(state)
            
            logger.info("\n📋 Step 2: Generating report outline")
            state = self.generate_report_outline(state)
            
            logger.info("\n🔍 Step 3: Generating section-specific queries")
            state = self.generate_section_queries(state)
            
            logger.info("\n🌐 Step 4: Performing web searches")
            state = self.perform_section_research(state)
            
            logger.info("\n✍️ Step 5: Writing section drafts")
            state = self.write_section_drafts(state)
            
            logger.info("\n🎨 Step 6: Formatting sections")
            state = self.format_sections(state)
            
            logger.info("\n📝 Step 7: Writing final sections")
            state = self.write_final_sections(state)
            
            logger.info("\n📦 Step 8: Compiling final report")
            state = self.compile_final_report(state)
            
            # Calculate processing time
            state.processing_time = time.time() - start_time
            
            logger.info("\n🎉 Agent execution completed successfully!")
            logger.info(f"Final report: {len(state.compiled_report)} characters")
            logger.info(f"Processing time: {state.processing_time:.2f} seconds")
            logger.info("="*60)
            
            return state
            
        except Exception as e:
            logger.error(f"⚠️ Agent execution failed: {e}")
            if 'state' in locals():
                state.error_messages.append(f"Pipeline execution failed: {str(e)}")
                state.processing_time = time.time() - start_time
                return state
            else:
                # Create error state
                error_state = AgentState(topic=topic)
                error_state.error_messages.append(f"Pipeline execution failed: {str(e)}")
                error_state.processing_time = time.time() - start_time
                return error_state


# Global research agent instance
research_agent = ResearchAgent() 