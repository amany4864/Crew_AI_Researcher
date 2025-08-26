# from fastapi import FastAPI
# from pydantic import BaseModel
# from crewai import Agent, Task, Crew, Process
# from crewai_tools import SerperDevTool
# import os
# import asyncio
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Check if SERPER_API_KEY is available
# serper_api_key = os.getenv("SERPER_API_KEY")
# if not serper_api_key:
#     raise ValueError("SERPER_API_KEY environment variable not set")

# # Initialize the tool
# tool = SerperDevTool()

# # Define the agents
# researcher = Agent(
#     role='Senior Research Analyst',
#     goal='Uncover cutting-edge developments in AI and data science',
#     backstory="""You work at a leading tech think tank.
#     Your expertise lies in identifying emerging trends.
#     You have a knack for dissecting complex data and presenting actionable insights.""",
#     verbose=True,
#     allow_delegation=False,
#     tools=[tool]
# )

# writer = Agent(
#     role='Content Writer',
#     goal='Craft compelling content on tech advancements',
#     backstory="""You are a renowned Content Strategist, known for your insightful and engaging articles.
#     You transform complex concepts into compelling narratives.""",
#     verbose=True,
#     allow_delegation=True
# )

# # Define the tasks
# def create_research_task(topic: str) -> Task:
#     return Task(
#         description=f"""Conduct a comprehensive analysis of the latest advancements in {topic}.
#         Identify key trends, breakthrough technologies, and potential industry impacts.
#         Your final answer must be a full analysis report.""",
#         expected_output='A comprehensive full analysis report on the latest advancements in the specified topic.',
#         agent=researcher
#     )

# def create_writing_task(topic: str) -> Task:
#     return Task(
#         description=f"""Using the insights provided, develop an engaging blog post that highlights the most significant advancements in {topic}.
#         Your post should be informative yet accessible, catering to a tech-savvy audience.
#         Make it sound cool, avoid complex words so it doesn't sound like AI.""",
#         expected_output=f'A well-written blog post on the topic of {topic}, based on the research analysis.',
#         agent=writer
#     )

# # Initialize FastAPI
# app = FastAPI()

# class Topic(BaseModel):
#     topic: str

# @app.post("/generate")
# async def generate_content(topic: Topic):
#     # Create the tasks
#     research_task = create_research_task(topic.topic)
#     writing_task = create_writing_task(topic.topic)

#     # Create the crew
#     crew = Crew(
#         agents=[researcher, writer],
#         tasks=[research_task, writing_task],
#         process=Process.sequential,
#         verbose=2,
#     )

#     # Run kickoff in a thread pool to avoid blocking
#     loop = asyncio.get_event_loop()
#     try:
#         result = await loop.run_in_executor(None, crew.kickoff)
#         return {"result": str(result)}
#     except Exception as e:
#         return {"error": str(e)}