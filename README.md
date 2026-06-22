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

F --> G{Campaign Type?}

G -->|Social Media| H[Generate Social Content]
G -->|Email Marketing| I[Generate Email Campaign]
G -->|Both| J[Generate Social Content and Email Campaign]

H --> K[Generate Content]
I --> L[Create Email Content]
J --> K
J --> L

K --> M{Need Media?}
M -->|Yes| N[Generate Media Assets]
M -->|No| O[Continue]

L --> P[Validate Email Content]
N --> Q[Validate Content]
O --> Q

P --> R[Schedule Email Campaign]
Q --> S[Schedule Publication]

R --> T[Send Email Campaign]
S --> U[Publish To Social Networks]

T --> V[Collect Analytics]
U --> V

V --> W[Optimization Suggestions]
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
  S --> G[Email Marketing Agent]

  A --> S
  B --> S
  C --> S
  D --> S
  E --> S
  F --> S
  G --> S

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
  E -->|Email Campaign| L[Email Marketing Agent]

  F --> M[Supervisor Review]
  G --> M
  H --> M
  I --> M
  J --> M
  K --> M
  L --> M

  M --> N{Approved?}
  N -->|No| B
  N -->|Yes| O[Continue Workflow]
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
  A[Need Media or Email Assets?] --> B{Asset Required?}

  B -->|No| C[Skip Asset Generation]
  B -->|Yes| D{Asset Type?}

  D -->|Single Image| E[Create Image Prompt]
  D -->|Carousel| F[Define Carousel Goal]
  D -->|PDF| G[Select PDF Template]
  D -->|Email Visual| H[Prepare Email Visual Asset]
  D -->|Other| I[Generate Alternative Media]

  E --> J[Generate Image]
  F --> K[Create Slide Outline]
  G --> L[Prepare PDF Content]
  H --> M[Design Email Asset]
  I --> N[Prepare Media Asset]

  J --> O[Check Image Quality]
  K --> P[Generate Slides]
  L --> Q[Render Layout]
  M --> R[Validate Email Asset]
  N --> S[Validate Alternative Media]

  O --> T{Approved?}
  P --> U[Check Visual Consistency]
  Q --> V[Validate Formatting]
  R --> W{Approved?}
  S --> X{Valid?}

  T -->|No| E
  T -->|Yes| Y[Save Image]

  U --> Z{Approved?}
  V --> AA{Approved?}
  W -->|No| H
  W -->|Yes| AB[Save Email Asset]
  X -->|No| I
  X -->|Yes| AC[Save Asset]

  Z -->|No| F
  Z -->|Yes| AD[Export Carousel Package]

  AA -->|No| G
  AA -->|Yes| AE[Export PDF]

  Y --> AF[Attach to Campaign]
  AD --> AF
  AE --> AF
  AB --> AF
  AC --> AF
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
