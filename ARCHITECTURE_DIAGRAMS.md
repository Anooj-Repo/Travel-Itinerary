# Architecture & Flow Diagrams
## Visual Reference for Presentation

---

## 1. SYSTEM ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Angular 17 Frontend (Port 4200)                  │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │
│  │  │  Document  │  │  Itinerary │  │   Search   │             │  │
│  │  │   Upload   │  │ Generation │  │  Interface │             │  │
│  │  │ Component  │  │ Component  │  │ Component  │             │  │
│  │  └────────────┘  └────────────┘  └────────────┘             │  │
│  │         │               │               │                     │  │
│  │         └───────────────┼───────────────┘                     │  │
│  │                         │                                     │  │
│  │              ┌──────────▼──────────┐                          │  │
│  │              │   API Service       │                          │  │
│  │              │  (HttpClient)       │                          │  │
│  │              └──────────┬──────────┘                          │  │
│  └───────────────────────────┼──────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                               │ HTTP/JSON
                               │ CORS Enabled
┌─────────────────────────────▼──────────────────────────────────────┐
│                      BACKEND-RAG SERVICE LAYER                      │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Flask REST API (Port 5001)                       │  │
│  │                                                               │  │
│  │  ┌────────────────┐         ┌────────────────┐              │  │
│  │  │  /api/rag/     │         │  /api/rag/     │              │  │
│  │  │   upload       │         │   generate     │              │  │
│  │  └───────┬────────┘         └────────┬───────┘              │  │
│  │          │                           │                       │  │
│  │          └───────────┬───────────────┘                       │  │
│  │                      │                                       │  │
│  │           ┌──────────▼──────────┐                            │  │
│  │           │   RAGService Class  │                            │  │
│  │           │  (rag_service.py)   │                            │  │
│  │           └──────────┬──────────┘                            │  │
│  └──────────────────────┼──────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
┌─────────▼──────┐ ┌──────▼──────┐ ┌────▼──────┐
│  PDF Processor │ │   Vector    │ │    LLM    │
│   (PDFMiner)   │ │   Store     │ │  Service  │
│                │ │  (FAISS)    │ │ (Mistral) │
│  Text Extract  │ │             │ │           │
│  Chunking      │ │  384-dim    │ │ 7B params │
│  1000 chars    │ │  Similarity │ │ Instruct  │
│  200 overlap   │ │  Search     │ │  Tuned    │
└────────┬───────┘ └──────┬──────┘ └────┬──────┘
         │                │              │
         │         ┌──────▼──────┐       │
         │         │ HuggingFace │       │
         │         │ Embeddings  │       │
         │         │             │       │
         │         │  all-MiniLM │       │
         │         │   -L6-v2    │       │
         │         │             │       │
         │         │  Local CPU  │       │
         │         │   Model     │       │
         │         └──────┬──────┘       │
         │                │              │
         └────────────────┼──────────────┘
                          │
              ┌───────────▼───────────┐
              │   LangChain Layer     │
              │                       │
              │  ┌─────────────────┐  │
              │  │ RetrievalQA     │  │
              │  │ Chain           │  │
              │  └─────────────────┘  │
              │                       │
              │  ┌─────────────────┐  │
              │  │ Text Splitter   │  │
              │  │ (Recursive)     │  │
              │  └─────────────────┘  │
              └───────────────────────┘
```

---

## 2. RAG PIPELINE FLOW

```
┌──────────────┐
│   PDF        │
│   Upload     │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 1: Text Extraction       │
│  ─────────────────────────     │
│  Tool: PDFMiner                │
│  Input: Binary PDF             │
│  Output: Raw text string       │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 2: Text Chunking         │
│  ─────────────────────────     │
│  Tool: LangChain Splitter      │
│  Chunk size: 1000 chars        │
│  Overlap: 200 chars            │
│  Strategy: Recursive           │
│  Output: List of chunks        │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 3: Embedding Generation  │
│  ─────────────────────────     │
│  Model: all-MiniLM-L6-v2       │
│  Dimension: 384                │
│  Runtime: Local CPU            │
│  Output: Vector embeddings     │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 4: Vector Storage        │
│  ─────────────────────────     │
│  Database: FAISS               │
│  Index type: Flat L2           │
│  Persistence: Disk             │
│  Path: ./data/faiss_travel_docs│
└──────┬─────────────────────────┘
       │
       │  ┌──────────────────┐
       │  │ User Query       │
       │  │ + Preferences    │
       │  └────────┬─────────┘
       │           │
       ▼           ▼
┌─────────────────────────────────┐
│  Step 5: Semantic Retrieval     │
│  ──────────────────────────     │
│  Query embedding generation     │
│  Similarity search (cosine)     │
│  Top-K retrieval (K=5)          │
│  Output: Relevant chunks        │
└──────┬──────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 6: Context Construction  │
│  ─────────────────────────     │
│  Combine retrieved chunks       │
│  Add user preferences           │
│  Build prompt template          │
│  Output: Full LLM prompt        │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 7: LLM Generation        │
│  ─────────────────────────     │
│  Model: Mistral-7B-Instruct    │
│  Provider: HuggingFace Router  │
│  Temperature: 0.7              │
│  Max tokens: 2048              │
│  Output: Structured itinerary  │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│  Step 8: Response Formatting   │
│  ─────────────────────────     │
│  Parse LLM output              │
│  Add source attribution         │
│  JSON structure                │
│  Return to frontend            │
└────────────────────────────────┘
```

---

## 3. DATA FLOW DIAGRAM

```
┌───────────────────────────────────────────────────────────────────┐
│                      DOCUMENT UPLOAD FLOW                          │
└───────────────────────────────────────────────────────────────────┘

User Action                 Backend Process              Storage
───────────                 ───────────────              ───────

[Select PDF]
     │
     ▼
[Click Upload]
     │
     │                 ┌──────────────────┐
     └────────────────>│ Validate File    │
     (FormData)        │ - Check type     │
                       │ - Secure name    │
                       │ - Size limit     │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Extract Text     │
                       │ (PDFMiner)       │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Chunk Text       │
                       │ (1000/200)       │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Generate         │
                       │ Embeddings       │      ┌──────────────┐
                       │ (384-dim)        │─────>│ FAISS Index  │
                       └────────┬─────────┘      │ .faiss file  │
                                │                └──────────────┘
                                ▼
                       ┌──────────────────┐
                       │ Save Metadata    │      ┌──────────────┐
                       │ - Filename       │─────>│ Metadata     │
                       │ - Chunks count   │      │ .pkl file    │
                       │ - Timestamp      │      └──────────────┘
                       └────────┬─────────┘
                                │
                                ▼
                          [Return JSON]
     ┌─────────────────────────┘
     │ {success: true,
     │  chunks: 145,
     │  filename: "guide.pdf"}
     ▼
[Display Success]


┌───────────────────────────────────────────────────────────────────┐
│                    ITINERARY GENERATION FLOW                       │
└───────────────────────────────────────────────────────────────────┘

User Input               Backend Process              AI Services
──────────               ───────────────              ───────────

[Form Submission]
- Destination
- Dates                  ┌──────────────────┐
- Budget        ────────>│ Parse Request    │
- Interests              └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Generate Query   │
                         │ Embedding        │    ┌──────────────┐
                         └────────┬─────────┘───>│ HuggingFace  │
                                  │               │ Embeddings   │
                                  │               └──────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ FAISS Search     │    ┌──────────────┐
                         │ Top-5 chunks     │<───│ Vector DB    │
                         └────────┬─────────┘    │ Similarity   │
                                  │               └──────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Build Prompt     │
                         │ - Context chunks │
                         │ - User prefs     │
                         │ - Instructions   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ LLM Generation   │    ┌──────────────┐
                         │ (Mistral-7B)     │───>│ HuggingFace  │
                         └────────┬─────────┘    │ Router API   │
                                  │               └──────────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Format Response  │
                         │ - Daily schedule │
                         │ - Activities     │
                         │ - Sources        │
                         └────────┬─────────┘
                                  │
                                  ▼
                            [Return JSON]
     ┌──────────────────────────┘
     │ {itinerary: {...},
     │  sources: [...],
     │  confidence: 0.95}
     ▼
[Display Itinerary]
```

---

## 4. COMPONENT INTERACTION DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                      ANGULAR FRONTEND                            │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │ RAG Itinerary │    │  Trip Form    │    │   Itinerary   │   │
│  │  Component    │    │  Component    │    │   Display     │   │
│  │               │    │               │    │  Component    │   │
│  │ - Upload UI   │    │ - Form inputs │    │ - Day view    │   │
│  │ - Doc list    │    │ - Validation  │    │ - Activities  │   │
│  │ - Search      │    │ - Submit      │    │ - Export      │   │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘   │
│          │                    │                    │            │
│          └────────────────────┼────────────────────┘            │
│                               │                                 │
│                    ┌──────────▼──────────┐                      │
│                    │   API Service       │                      │
│                    │                     │                      │
│                    │ - HttpClient        │                      │
│                    │ - Error handling    │                      │
│                    │ - Type safety       │                      │
│                    └──────────┬──────────┘                      │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                        HTTP Requests
                     (JSON over CORS)
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                       FLASK BACKEND                               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    app.py (Routes)                          │  │
│  │                                                             │  │
│  │  ┌─────────────────┐          ┌─────────────────┐          │  │
│  │  │ @app.route(     │          │ @app.route(     │          │  │
│  │  │ '/api/rag/      │          │ '/api/rag/      │          │  │
│  │  │  upload')       │          │  generate')     │          │  │
│  │  │                 │          │                 │          │  │
│  │  │ - Validate file │          │ - Parse JSON    │          │  │
│  │  │ - Call service  │          │ - Call service  │          │  │
│  │  │ - Return JSON   │          │ - Return JSON   │          │  │
│  │  └────────┬────────┘          └────────┬────────┘          │  │
│  └───────────┼─────────────────────────────┼──────────────────┘  │
│              │                             │                     │
│              └──────────┬──────────────────┘                     │
│                         │                                        │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │              RAGService (rag_service.py)                   │  │
│  │                                                            │  │
│  │  ┌────────────────────┐      ┌────────────────────┐      │  │
│  │  │ upload_document()  │      │ generate_rag_      │      │  │
│  │  │                    │      │  itinerary()       │      │  │
│  │  │ - Extract text     │      │ - Build retriever  │      │  │
│  │  │ - Chunk content    │      │ - Search vectors   │      │  │
│  │  │ - Create embeddings│      │ - Create prompt    │      │  │
│  │  │ - Update FAISS     │      │ - Call LLM         │      │  │
│  │  └────────┬───────────┘      └────────┬───────────┘      │  │
│  └───────────┼─────────────────────────────┼────────────────┘  │
└──────────────┼─────────────────────────────┼───────────────────┘
               │                             │
      ┌────────▼────────┐           ┌────────▼────────┐
      │  FAISS Vector   │           │  LLM API        │
      │  Store          │           │  (HuggingFace)  │
      │                 │           │                 │
      │ - Indexing      │           │ - Chat model    │
      │ - Similarity    │           │ - Streaming     │
      │ - Persistence   │           │ - Temperature   │
      └─────────────────┘           └─────────────────┘
```

---

## 5. FUTURE STATE ARCHITECTURE (Microsoft 365 Integration)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MICROSOFT 365 ECOSYSTEM                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Teams     │  │   Outlook    │  │  SharePoint  │          │
│  │   Channel    │  │   Calendar   │  │   Library    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│              ┌────────────▼────────────┐                        │
│              │ Microsoft 365 Copilot   │                        │
│              │                         │                        │
│              │ - Natural language UI   │                        │
│              │ - Context awareness     │                        │
│              │ - Enterprise SSO        │                        │
│              └────────────┬────────────┘                        │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                   Plugin/Agent API
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Microsoft Semantic Kernel / Prompt Flow         │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │   Planner   │  │   Memory    │  │   Skills    │      │   │
│  │  │   Agent     │  │   Manager   │  │  Registry   │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬──────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼─────────┐  ┌──────────▼──────────┐  ┌────────▼────────┐
│ Power Automate  │  │ Azure AI Search     │  │ Azure OpenAI    │
│                 │  │                     │  │                 │
│ - Approval flow │  │ - Hybrid search     │  │ - GPT-4 Turbo   │
│ - Notifications │  │ - Vector + keyword  │  │ - Embeddings    │
│ - Integrations  │  │ - Security trimming │  │ - Fine-tuning   │
└─────────────────┘  └──────────┬──────────┘  └─────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  SharePoint Online  │
                     │  Document Libraries │
                     │                     │
                     │ - Version control   │
                     │ - Metadata          │
                     │ - Permissions       │
                     └─────────────────────┘
```

---

## 6. SECURITY & COMPLIANCE FLOW

```
┌────────────────────────────────────────────────────────────────┐
│                       USER REQUEST                              │
│          "Generate itinerary for Paris next week"               │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Authentication     │
                  │ - Azure AD SSO     │
                  │ - Token validation │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Authorization      │
                  │ - RBAC check       │
                  │ - Resource access  │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Input Validation   │
                  │ - Sanitization     │
                  │ - Type checking    │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Rate Limiting      │
                  │ - Request throttle │
                  │ - Quota check      │
                  └────────┬───────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
        ┌───────▼────────┐   ┌────────▼────────┐
        │  Vector Search │   │   LLM Query     │
        │  (Encrypted)   │   │  (PII filtered) │
        └───────┬────────┘   └────────┬────────┘
                │                     │
                └──────────┬──────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Response Filter    │
                  │ - PII redaction    │
                  │ - Content policy   │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Audit Logging      │
                  │ - Request details  │
                  │ - Response time    │
                  │ - User identity    │
                  └────────┬───────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ Response to User   │
                  │ (Encrypted transit)│
                  └────────────────────┘
```

---

## 7. SCALABILITY EVOLUTION

```
┌──────────────────────────────────────────────────────────────────┐
│                         PHASE 1: POC                             │
│                     (Current Implementation)                      │
│                                                                  │
│      ┌────────────┐         ┌────────────┐                      │
│      │  Angular   │◄───────►│   Flask    │                      │
│      │  (Port     │         │  (Port     │                      │
│      │   4200)    │         │   5001)    │                      │
│      └────────────┘         └─────┬──────┘                      │
│                                   │                              │
│                           ┌───────▼────────┐                     │
│                           │ FAISS (Local)  │                     │
│                           └────────────────┘                     │
│                                                                  │
│  Capacity: 50 users | Storage: 10GB | Latency: <500ms           │
└──────────────────────────────────────────────────────────────────┘

                            ↓ EVOLVE ↓

┌──────────────────────────────────────────────────────────────────┐
│                      PHASE 2: CONTAINERIZED                       │
│                    (Docker + Kubernetes)                          │
│                                                                  │
│  ┌────────────┐                                                  │
│  │   Nginx    │  Load Balancer                                   │
│  │   Ingress  │                                                  │
│  └─────┬──────┘                                                  │
│        │                                                         │
│    ┌───▼────┐─────┬─────────┬─────────┐                         │
│    │        │     │         │         │                         │
│  ┌─▼──┐  ┌─▼──┐ ┌─▼──┐   ┌─▼──┐   ┌─▼──┐                       │
│  │Pod1│  │Pod2│ │Pod3│   │Pod4│   │Pod5│  (Auto-scaling)       │
│  └─┬──┘  └─┬──┘ └─┬──┘   └─┬──┘   └─┬──┘                       │
│    └───────┴─────┴─────────┴─────────┘                          │
│                    │                                             │
│             ┌──────▼───────┐                                     │
│             │ Shared FAISS │  (Persistent Volume)                │
│             │   Storage    │                                     │
│             └──────────────┘                                     │
│                                                                  │
│  Capacity: 500 users | Storage: 100GB | Latency: <200ms         │
└──────────────────────────────────────────────────────────────────┘

                            ↓ EVOLVE ↓

┌──────────────────────────────────────────────────────────────────┐
│                  PHASE 3: CLOUD-NATIVE AZURE                     │
│                  (Enterprise Production)                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Azure Front Door (CDN + WAF)                 │   │
│  └───────────────────────────┬──────────────────────────────┘   │
│                              │                                   │
│          ┌───────────────────┼───────────────────┐              │
│          │                   │                   │              │
│    ┌─────▼──────┐     ┌──────▼──────┐    ┌──────▼──────┐       │
│    │   App      │     │     App     │    │     App     │       │
│    │  Service   │     │   Service   │    │   Service   │       │
│    │  (Region1) │     │  (Region2)  │    │  (Region3)  │       │
│    └─────┬──────┘     └──────┬──────┘    └──────┬──────┘       │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              │                                   │
│                   ┌──────────▼──────────┐                        │
│                   │   Azure AI Search   │                        │
│                   │   (Multi-region)    │                        │
│                   │                     │                        │
│                   │ - Vector indexing   │                        │
│                   │ - Hybrid search     │                        │
│                   │ - Auto-scaling      │                        │
│                   └──────────┬──────────┘                        │
│                              │                                   │
│                   ┌──────────▼──────────┐                        │
│                   │  Blob Storage       │                        │
│                   │  (Document archive) │                        │
│                   └─────────────────────┘                        │
│                                                                  │
│  Capacity: 10K+ users | Storage: 10TB+ | Latency: <100ms        │
│  Features: Multi-region | Auto-scaling | 99.99% SLA             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. MONITORING & OBSERVABILITY

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION METRICS                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Frontend   │    │   Backend    │    │   AI Layer   │
│   Metrics    │    │   Metrics    │    │   Metrics    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       ├───────────────────┼───────────────────┤
       │                   │                   │
       │     ┌─────────────▼─────────────┐     │
       │     │  Azure Application        │     │
       └────►│  Insights                 │◄────┘
             │                           │
             │ - Request telemetry       │
             │ - Exception tracking      │
             │ - Custom events           │
             │ - Performance counters    │
             └───────────┬───────────────┘
                         │
                         ▼
             ┌───────────────────────────┐
             │   Azure Monitor           │
             │   (Dashboards)            │
             │                           │
             │ KPIs Tracked:             │
             │ ✓ Request rate            │
             │ ✓ Response time (P50/P95) │
             │ ✓ Error rate              │
             │ ✓ Document upload success │
             │ ✓ Vector search latency   │
             │ ✓ LLM generation time     │
             │ ✓ Active users            │
             │ ✓ Storage utilization     │
             └───────────────────────────┘
```

---

*These diagrams provide visual reference for technical presentations and documentation*  
*Use in combination with PRESENTATION_SLIDES.md for complete narrative*
