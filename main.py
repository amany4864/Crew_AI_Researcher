# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field
# from crewai import Agent, Task, Crew, Process, LLM
# from crewai_tools import SerperDevTool


# import re
# import os
# import asyncio
# import logging
# from typing import Optional, Dict, Any, List
# from datetime import datetime
# import uuid
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Validate required environment variables
# required_vars = ["SERPER_API_KEY", "GOOGLE_API_KEY","OPENAI_API_KEY"]
# missing_vars = [var for var in required_vars if not os.getenv(var)]
# if missing_vars:
#     raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# # Initialize Gemini LLM

# myllm= LLM(
#     model="gpt-3.5-turbo",
#     api_key=os.getenv("OPENAI_API_KEY")
# )
# # gemini_llm = LLM(
# #     model="gemini-1.5-flash",  
# #     api_key=os.getenv("GOOGLE_API_KEY")
# # )
# # Initialize Groq LLM
# # groq_llm = LLM(
# #     model="groq/compound-beta",  # or "groq/mixtral-8x7b-   instruct"
# #     api_key=os.getenv("GROQ_API_KEY")
# # )


# # Initialize tools
# serper_tool = SerperDevTool()

# class ContentRequest(BaseModel):
#     topic: str = Field(..., min_length=3, max_length=200)
#     content_type: Optional[str] = Field(default="blog_post")
#     word_count: Optional[int] = Field(default=800, ge=20, le=2000)

# class ContentResponse(BaseModel):
#     id: str
#     topic: str
#     content: str
#     citations: List[Dict[str, Any]]
#     generated_at: datetime
#     metadata: Dict[str, Any]

# # In-memory storage
# content_storage: Dict[str, Dict[str, Any]] = {}

# class ContentService:
#     def __init__(self):
#         # Researcher Agent - Uses Serper for web search only
#         self.researcher = Agent(
#             role='Senior Research Analyst',
#             goal='Conduct thorough research using credible web sources',
#             backstory="""You are an experienced research analyst who excels at finding 
#             the latest information from web sources, industry news, and reports.      
#             You provide comprehensive, evidence-based insights.""",
#             verbose=True,
#             allow_delegation=False,
#             tools=[serper_tool],
#             llm=myllm
#         )
        
#         # Writer Agent - Creates content based on research
#         self.writer = Agent(
#             role='Expert Content Writer',
#             goal='Create engaging, well-structured content based on research',
#             backstory="""You are a professional content writer who transforms research 
#             into compelling, accessible content. You write clearly and engagingly for 
#             your target audience.""",
#             verbose=True,
#             allow_delegation=False,
#             llm=myllm
#         )
#     def create_research_task(self, request: ContentRequest) -> Task:
#         return Task(
#             description=f"""
#             Research the topic: {request.topic}
            
#             Use web search to find:
#             - Latest news, trends, and industry developments
#             - Key facts, statistics, and data points
#             - Expert insights and opinions
#             - Practical applications and real-world examples
            
#             IMPORTANT: For every source you find, collect the following citation information:
#             - Title of article
#             - Author(s) or organization
#             - Publication date
#             - URL
#             - Source type (web)
            
#             Format your research with clear source attributions and prepare a bibliography.
#             Prioritize recent and credible sources.
#             """,
#             expected_output="""A comprehensive research report with:
#             1. Key findings and insights
#             2. Statistics and data points
#             3. Industry trends and developments
#             4. A complete bibliography with all sources cited in this format:
#                - [1] Title | Author | Date | URL | Web
#                - [2] Title | Author | Date | URL | Web
#                etc.""",
#             agent=self.researcher
#         )
    
#     def create_writing_task(self, request: ContentRequest) -> Task:
#         return Task(
#             description=f"""
#             Create a {request.content_type} about: {request.topic}
            
#             Requirements:
#             - Approximately {request.word_count} words
#             - Include engaging headline
#             - Well-structured with subheadings
#             - Clear introduction and conclusion
#             - Based on the research findings provided
#             - Write in a professional yet accessible tone
            
#             CITATION REQUIREMENTS:
#             - Use in-text citations in the format [1], [2], etc.
#             - Reference specific claims, statistics, and research findings
#             - Include a "References" section at the end
#             - Make sure every citation number corresponds to the research bibliography
#             - Use citations naturally within the content flow
#             """,
#             expected_output=f"""A well-written {request.content_type} of approximately {request.word_count} words that includes:
#             1. Engaging title and introduction
#             2. Well-structured main content with subheadings
#             3. In-text citations [1], [2], etc. for all claims and statistics
#             4. Professional conclusion
#             5. Complete References section at the end
#             6. Proper citation formatting throughout""",
#             agent=self.writer
#         )

#     # def extract_citations(self,content: str):
#     #     citations = []
#     #     # Match "[1]" at the start of the line, capture the rest
#     #     pattern = re.compile(r"^\[(\d+)\]\s*(.*)$", re.MULTILINE)

#     #     for match in pattern.finditer(content):
#     #         num = int(match.group(1))
#     #         rest = match.group(2).strip()

#     #         # Handle placeholder citations
#     #         if rest.lower().startswith("[insert citation here"):
#     #             citations.append({
#     #                 "number": num,
#     #                 "title": rest,
#     #                 "author": None,
#     #                 "date": None,
#     #                 "url": None,
#     #                 "type": "Placeholder"
#     #             })
#     #         else:
#     #             citations.append({
#     #                 "number": num,
#     #                 "title": rest,
#     #                 "author": None,
#     #                 "date": None,
#     #                 "url": None,
#     #                 "type": "Web"
#     #             })
#     #     return citations

#     def extract_citations(self, content: str) -> List[Dict[str, Any]]:
#         """Extract citations from the References section of the generated content"""
#         citations = []
#         lines = content.splitlines()
#         in_references = False
#         citation_count = 0

#         for line in lines:
#             line = line.strip()

#             # Detect references section start (handles "# References", "## References", "**References**")
#             if not in_references and "references" in line.lower():
#                 in_references = True
#                 continue

#             # Parse only after references section begins
#             if in_references and line.startswith("["):
#                 try:
#                     # Example format:
#                     # [1] Title | Author | Date | URL
#                     parts = [p.strip() for p in line.split("|")]
#                     if len(parts) >= 4:
#                         citation_count += 1
#                         number = citation_count
#                         title = parts[0].split("]", 1)[-1].strip()  # remove "[1]"
#                         author = parts[1]
#                         date = parts[2]
#                         url = parts[3]

#                         citations.append({
#                             "number": number,
#                             "title": title,
#                             "author": author,
#                             "date": date,
#                             "url": url,
#                             "type": "Web"
#                         })
#                 except Exception as e:
#                     logger.warning(f"Failed to parse citation: {line}, Error: {e}")

#         return citations

    

#     def link_citations(self,content: str, citations: List[Dict[str, Any]]) -> str:
#         """
#         Replace in-text [n] citations with clickable links using the extracted citations list.
#         Example: [1] -> <a href="https://example.com" target="_blank">[1]</a>
#         """
#         def replacer(match):
#             num = int(match.group(1))
#             for c in citations:
#                 if c["number"] == num and c.get("url"):
#                     return f'<a href="{c["url"]}" target="_blank">[{num}]</a>'
#             return match.group(0)  # fallback: keep [n] as-is

#         # Replace all [n] patterns where n is 1–3 digits
#         return re.sub(r"\[(\d{1,3})\]", replacer, content)


#     async def generate_content(self, request: ContentRequest) -> Dict[str, Any]:
#         try:
#             research_task = self.create_research_task(request)
#             writing_task = self.create_writing_task(request)
            
#             crew = Crew(
#                 agents=[self.researcher, self.writer],
#                 tasks=[research_task, writing_task],
#                 process=Process.sequential,
#                 verbose=True
#             )
            
#             loop = asyncio.get_event_loop()
#             result = await loop.run_in_executor(None, crew.kickoff)
            
#             content_str = str(result)
#             citations = self.extract_citations(content_str)
#             linked_content = self.link_citations(content_str, citations)
            
#             return {
#                 "content": content_str,
#                 "citations": citations,
#                 "research_summary": str(research_task.output) if hasattr(research_task, 'output') else "Research completed"
#             }
            
#         except Exception as e:
#             logger.error(f"Content generation failed: {str(e)}")
#             raise

# # Initialize service and app
# content_service = ContentService()
# app = FastAPI(title="AI Content Generator", version="1.0.0")

# # Add CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# async def root():
#     return {"message": "AI Content Generator API", "status": "running"}

# @app.post("/generate")
# async def generate_content(request: ContentRequest):
#     try:
#         job_id = str(uuid.uuid4())
#         result = await content_service.generate_content(request)
        
#         content_data = {
#             "id": job_id,
#             "topic": request.topic,
#             "content": result["content"],
#             "citations": result["citations"],
#             "generated_at": datetime.now(),
#             "metadata": {
#                 "content_type": request.content_type,
#                 "word_count": request.word_count,
#                 "actual_words": len(result["content"].split()),
#                 "total_citations": len(result["citations"])
#             }
#         }
        
#         content_storage[job_id] = content_data
        
#         return ContentResponse(**content_data)
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/content/{content_id}")
# async def get_content(content_id: str):
#     if content_id not in content_storage:
#         raise HTTPException(status_code=404, detail="Content not found")
#     return ContentResponse(**content_storage[content_id])

# @app.get("/content")
# async def get_all_content():
#     return {"total": len(content_storage), "content": list(content_storage.values())}

# @app.delete("/content/{content_id}")
# async def delete_content(content_id: str):
#     if content_id not in content_storage:
#         raise HTTPException(status_code=404, detail="Content not found")
#     del content_storage[content_id]
#     return {"message": "Content deleted"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
