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
```mermaid
flowchart TD
  U[User] --> S[Supervisor / Orchestrator]

  S --> A[Strategy Agent]
  S --> B[Content Agent]
  S --> C[Media Agent]
  S --> D[Scheduling Agent]
  S --> E[Publishing Agent]
  S --> F[Analytics Agent]

  A --> S
  B --> S
  C --> S
  D --> S
  E --> S
  F --> S

  S --> O[Final Campaign Output]
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
```
2) Campaign planning flow
```mermaid
flowchart TD
  A[Marketing Strategy] --> B[Define Campaign Goals]
  B --> C[Select Target Audience]
  C --> D[Choose Channels]
  D --> E[Set Content Themes]
  E --> F[Build Campaign Calendar]
  F --> G[Campaign Plan Ready]
```
3) Content generation flow
```mermaid
flowchart TD
  A[Campaign Plan] --> B[Create Content Brief]
  B --> C[Generate Draft Content]
  C --> D[Check Tone and Brand Voice]
  D --> E{Valid?}

  E -->|No| F[Revise Draft]
  F --> C

  E -->|Yes| G[Adapt for Platform]
  G --> H[Final Content Output]
  ``` 
4) Media Generation diagram
```mermaid
flowchart TD
  A[Need Media?] --> B{Media Required?}

  B -->|No| C[Skip Media Generation]
  B -->|Yes| D{Media Type?}

  D -->|Single Image| E[Create Image Prompt]
  D -->|Carousel| F[Define Carousel Goal]
  D -->|PDF| G[Select PDF Template]
  D -->|Other| H[Generate Alternative Media]

  E --> I[Generate Image]
  F --> J[Create Slide Outline]
  G --> K[Prepare PDF Content]
  H --> L[Prepare Media Asset]

  I --> M[Check Image Quality]
  J --> N[Generate Slides]
  K --> O[Render Layout]
  L --> P[Validate Alternative Media]

  M --> Q{Approved?}
  N --> R[Check Visual Consistency]
  O --> S[Validate Formatting]
  P --> T{Valid?}

  Q -->|No| E
  Q -->|Yes| U[Save Image]

  R --> V{Approved?}
  S --> W{Approved?}
  T -->|No| D
  T -->|Yes| X[Save Asset]

  V -->|No| F
  V -->|Yes| Y[Export Carousel Package]

  W -->|No| G
  W -->|Yes| Z[Export PDF]

  U --> AA[Attach to Campaign]
  Y --> AA
  Z --> AA
  X --> AA
  ``` 
5) Publishing flow
```mermaid
   flowchart TD
  A[Final Content + Media] --> B[Validate Assets]
  B --> C[Select Publish Time]
  C --> D[Format for Platform]
  D --> E[Publish to Social Network]
  E --> F[Confirm Publication]
  ```
6) Analytics and optimization loop
```mermaid
flowchart TD
  A[Published Campaign] --> B[Collect Analytics]
  B --> C[Measure Performance]
  C --> D[Generate Insights]
  D --> E[Optimization Suggestions]
  E --> F[Update Strategy]
  F --> G[Next Campaign]
  ```
