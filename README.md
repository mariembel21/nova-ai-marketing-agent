# Nova AI Marketing Agent

 An AI-powered backend for marketing strategy generation, social media content creation, profile optimization, and multi-platform publishing.

Nova AI Marketing Agent is a backend application designed to assist businesses with digital marketing workflows through AI-powered generation and social media automation.

The system combines **FastAPI**, **LangGraph**, **Groq LLMs**, **PostgreSQL**, and social-media APIs to provide structured AI workflows for marketing strategy, content creation, professional bio generation, presentation planning, and social-media publishing.

The project was developed with a focus on building a modular, API-first backend architecture where AI capabilities and external social-media integrations can be exposed through reusable services and validated REST APIs.

---

##  Key Features

### AI-Powered Marketing Workflows

The backend currently provides four specialized AI agents:

- **Strategy Agent**
  - Generates structured marketing strategies
  - Defines market positioning and value propositions
  - Identifies target personas and acquisition channels
  - Builds conversion funnels
  - Produces 30/60/90-day action plans
  - Defines relevant marketing KPIs
  - Supports strategy revision based on client feedback

- **Content Agent**
  - Generates social-media content
  - Produces platform-specific content
  - Adapts prompts according to the selected social network
  - Supports structured content generation and validation

- **Bio Agent**
  - Analyzes professional profile information
  - Generates optimized profile biographies
  - Produces multiple alternative versions for comparison

- **Presentation Agent**
  - Generates structured presentation outlines
  - Produces an 11-slide presentation structure
  - Validates generated presentation content
  - Supports controlled revision of generated structures

Each agent is implemented as a **LangGraph workflow** and communicates with the LLM layer through a reusable provider abstraction.

---

##  AI Architecture

The AI layer is built around **LangGraph** and a provider abstraction that separates agent logic from the underlying LLM provider.

The current implementation uses:

- **LangGraph** — agent workflow orchestration
- **Groq API** — LLM inference
- **Llama 3.3 70B Versatile** — default language model
- **Pydantic** — structured input/output validation
- **Python** — core implementation

Generated responses are structured and validated using Pydantic models rather than being returned as unrestricted text.

### AI Request Flow

```mermaid
flowchart LR
    A[Client Request] --> B[FastAPI Route]
    B --> C[Specialized Agent]
    C --> D[LangGraph Workflow]
    D --> E[Prompt Construction]
    E --> F[Groq LLM]
    F --> G[Structured JSON Response]
    G --> H[Pydantic Validation]
    H --> I[API Response]
