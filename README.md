# AI Content Generator

This project is an AI-powered content generation API built with Python and FastAPI. It utilizes a "crew" of AI agents to automate the process of researching and writing content on a given topic.

**GitHub Repository:** [https://github.com/amany4864/Crew_AI_Researcher](https://github.com/amany4864/Crew_AI_Researcher)

Deployed on :- [https://blaze-ink-psi.vercel.app/](https://blaze-ink-psi.vercel.app/)


## Workflow

1.  **API Request:** A user sends a POST request to the `/generate` endpoint with a JSON payload containing:
    *   `topic` (string): The desired topic for the content.
    *   `content_type` (string, optional): The type of content to generate (e.g., "blog\_post").
    *   `word_count` (integer, optional): The approximate desired word count.

2.  **AI Crew:** The application initializes a "crew" of two AI agents:
    *   **Researcher Agent:** This agent uses the SerperDevTool to conduct web searches and gather information about the requested topic. It focuses on finding credible sources, latest news, and key data.
    *   **Writer Agent:** This agent takes the research findings from the researcher and crafts a well-structured and engaging piece of content. It can generate different types of content, such as blog posts.

3.  **Content Generation:** The two agents work in a sequential process:
    *   The researcher gathers information and creates a research report with citations.
    *   The writer uses the research report to write the final content, including in-text citations.

4.  **Citation Extraction and Linking:** The application extracts the citations from the generated content and links them to the corresponding URLs.

5.  **API Response:** The API returns a JSON response containing:
    *   `id`: A unique ID for the generated content.
    *   `topic`: The original topic.
    *   `content`: The generated content with linked citations.
    *   `citations`: A list of the sources used.
    *   `generated_at`: The timestamp of when the content was generated.
    *   `metadata`: Additional information about the content.

## Endpoints

*   `GET /`: Returns the status of the API.
*   `POST /generate`: Generates new content.
*   `GET /content/{content_id}`: Retrieves previously generated content by its ID.
*   `GET /content`: Retrieves all previously generated content.
*   `DELETE /content/{content_id}`: Deletes previously generated content by its ID.

## Technology Stack

*   **Backend:** Python, FastAPI
*   **AI Framework:** `crewai`
*   **LLM:** Gemini
*   **Dependencies:**
    *   `fastapi`: Web framework.
    *   `uvicorn`: ASGI server.
    *   `litellm`: Library for interacting with LLMs.
    *   `crewai`: Framework for orchestrating AI agents.
    *   `python-dotenv`: For managing environment variables.
*   **Testing:** `unittest`
*   **Deployment:** Docker

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set up environment variables:** Create a `.env` file with the following:
    ```
    SERPER_API_KEY="your_serper_api_key"
    GOOGLE_API_KEY="your_google_api_key"
    ```
3.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
4.  **Run tests:**
    ```bash
    python test.py
    ```
5.  **Build and run with Docker:**
    ```bash
    docker build -t ai-content-generator .
    docker run -p 8000:8000 -v ./.env:/app/.env ai-content-generator
    ```
