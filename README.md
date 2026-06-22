# nova-ai-marketing-agent
AI-powered marketing and social media automation agent for content generation, campaign planning, image creation, scheduling, and analytics.

## Workflow
```mermaid
flowchart TD

A[User Request] --> B[Validate Input]

B --> C[Generate Marketing Strategy]

C --> D{Strategy Valid?}

D -->|No| E[Ask User For Missing Data]
E --> B

D -->|Yes| F[Create Campaign Plan]

F --> G[Generate Content]

G --> H{Need Image?}

H -->|Yes| I[Generate Image]

H -->|No| J[Continue]

I --> K[Validate Content]
J --> K

K --> L[Schedule Publication]

L --> M[Publish To Social Networks]

M --> N[Collect Analytics]

N --> O[Optimization Suggestions]
```
1) Supervisor orchestration flow
```mermaid
flowchart TD
  A[User Request] --> B[Supervisor]
  B --> C{Request Valid?}

  C -->|No| D[Ask for Missing Data]
  D --> A

  C -->|Yes| E{What is Needed?}

  E -->|Strategy| F[Strategy Agent]
  E -->|Content| G[Content Agent]
  E -->|Media| H[Media Agent]
  E -->|Scheduling| I[Scheduling Agent]
  E -->|Publishing| J[Publishing Agent]
  E -->|Analytics| K[Analytics Agent]

  F --> L[Supervisor Review]
  G --> L
  H --> L
  I --> L
  J --> L
  K --> L

  L --> M{Approved?}
  M -->|No| B
  M -->|Yes| N[Continue Workflow]
