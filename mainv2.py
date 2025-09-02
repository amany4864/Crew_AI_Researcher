from fastapi import FastAPI, HTTPException, Response, Cookie, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

import os
import anyio
import logging
import uuid
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from db import ContentDB  # Import our simple DB module

# -------------------- ENV & LOGGING --------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

required_vars = ["SERPER_API_KEY", "OPENAI_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# -------------------- INIT LLM, TOOLS & DB --------------------
myllm = LLM(
    model="gpt-3.5-turbo",
    api_key=os.getenv("OPENAI_API_KEY")
)
serper_tool = SerperDevTool()
db = ContentDB()

# -------------------- MODELS --------------------
class ContentRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    content_type: Optional[str] = Field(default="blog_post")
    word_count: Optional[int] = Field(default=800, ge=20, le=2000)

class ContentResponse(BaseModel):
    id: str
    topic: str
    content: str
    citations: List[Dict[str, Any]]
    generated_at: datetime
    metadata: Dict[str, Any]

# -------------------- SERVICE --------------------
class ContentService:
    def __init__(self):
        self.researcher = Agent(
            role="Senior Research Analyst",
            goal="Conduct thorough research using credible web sources",
            backstory="""You are an experienced research analyst who excels at finding 
            the latest information from web sources, industry news, and reports.""",
            verbose=True,
            allow_delegation=False,
            tools=[serper_tool],
            llm=myllm,
        )
        self.writer = Agent(
            role="Expert Content Writer",
            goal="Create engaging, well-structured content based on research",
            backstory="""You are a professional content writer who transforms research 
            into compelling, accessible content.""",
            verbose=True,
            allow_delegation=False,
            llm=myllm,
        )

    def create_research_task(self, request: ContentRequest) -> Task:
        return Task(
            description=f"Research the topic: {request.topic}\n\n"
            "Use web search to find:\n"
            "- Latest news, trends, and industry developments\n"
            "- Key facts, statistics, and data points\n"
            "- Expert insights and opinions\n"
            "- Practical applications and real-world examples\n\n"
            "IMPORTANT: Collect citation info (Title | Author | Date | URL | Web).",
            expected_output="""A research report with:
            1. Key findings
            2. Statistics
            3. Trends
            4. Bibliography""",
            agent=self.researcher,
        )

    def create_writing_task(self, request: ContentRequest) -> Task:
        return Task(
            description=f"""
            Create a {request.content_type} about: {request.topic}
            
            Requirements:
            - ~{request.word_count} words
            - Engaging headline
            - Structured with subheadings
            - Clear intro & conclusion
            - Based on research findings
            - Use in-text citations [1], [2], etc.
            """,
            expected_output="A polished article with proper citations & references.",
            agent=self.writer,
        )

    def extract_citations(self, content: str) -> List[Dict[str, Any]]:
        citations = []
        lines = content.splitlines()
        in_references = False
        citation_count = 0

        for line in lines:
            line = line.strip()
            if not in_references and "references" in line.lower():
                in_references = True
                continue

            if in_references and line.startswith("["):
                try:
                    # Format: [1] Title | Author | Date | URL | Web
                    match = re.match(r"^\[\d+\]\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)$", line)
                    if match:
                        citation_count += 1
                        citations.append({
                            "number": citation_count,
                            "title": match.group(1),
                            "author": match.group(2),
                            "date": match.group(3),
                            "url": match.group(4),
                            "type": "Web",
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse citation: {line}, Error: {e}")

        return citations

    async def generate_content(self, request: ContentRequest) -> Dict[str, Any]:
        research_task = self.create_research_task(request)
        writing_task = self.create_writing_task(request)

        crew = Crew(
            agents=[self.researcher, self.writer],
            tasks=[research_task, writing_task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = await anyio.to_thread.run_sync(crew.kickoff)
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise HTTPException(status_code=500, detail="Content generation failed")

        content_str = str(result)
        citations = self.extract_citations(content_str)

        return {
            "content": content_str,
            "citations": citations,
            "research_summary": str(getattr(research_task, "output", "Research completed")),
        }

# -------------------- APP --------------------
content_service = ContentService()
app = FastAPI(title="AI Content Generator", version="1.0.0")

# CORS

origins = [
    "https://blaze-ink-psi.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",  # ⚡ remove space
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # must be specific when using credentials
    allow_credentials=True, # allow cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "AI Content Generator API", "status": "running"}

@app.post("/generate")
async def generate_content(
    request: ContentRequest, response: Response, session_id: Optional[str] = Cookie(None)
):
    # Create session if not exists
    # if not session_id:
    if True:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="Lax",
            secure=True
        )
    else:
        # 🔒 Block further requests for this session
        existing_content = db.get_session_content(session_id)
        if existing_content:
            raise HTTPException(
                status_code=403,
                detail="You can only generate content once per session"
            )

    job_id = str(uuid.uuid4())
    result = await content_service.generate_content(request)

    content_data = {
        "id": job_id,
        "topic": request.topic,
        "content": result["content"],
        "citations": result["citations"],
        "generated_at": datetime.now(),
        "metadata": {
            "content_type": request.content_type,
            "word_count": request.word_count,
            "actual_words": len(re.findall(r'\w+', result["content"])),
            "total_citations": len(result["citations"]),
        },
    }

    db.save_content(session_id, content_data)
    return ContentResponse(**content_data)

# 🔥 Get all content with pagination (no session filter)
@app.get("/all-content")
async def get_all_content(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    all_content = db.get_all_content()
    total = len(all_content)
    paginated = all_content[skip: skip + limit]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "content": paginated,
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # use Render's PORT or default to 8000 locally
    uvicorn.run(app, host="0.0.0.0", port=port)
