Excellent. You have a robust, synchronous `LLMService` class. Now, let's build on that foundation.

You've described a sophisticated, iterative process. The key is to break it down into a stateful, sequential workflow where each step is a distinct API interaction. The backend will be responsible for managing the state of the document generation project from start to finish.

Here is a complete, amended, and sequential workflow that fills the logical gaps, particularly around state management, asynchronous tasks, and the user interaction loop.

---

### The Complete Document Generation Workflow

This workflow is built around a central concept: a **`ProjectSession`**. Every time a user starts a new document, a unique session is created on the backend. This session holds all the artifacts related to that document: the initial prompt, the generated plan, the content for each section, user edits, and all associated metadata (entities, risks, etc.). This state will be managed by your `document_manager.py`.

---

#### **Phase 1: Project Initiation & Input Ingestion**

This is the starting point. The user provides their initial request, which can be simple text or a reference document.

*   **Trigger:** User enters a prompt and/or uploads a file in the UI and clicks "Start Project".
*   **API Endpoint:** `POST /api/v1/projects`
*   **Backend Actions:**
    1.  Call `document_manager.create_session()` to create a new, unique project directory (e.g., `/resources/tmp_data_store/<session_id>`).
    2.  Save the user's initial text prompt to a file (e.g., `00_initial_prompt.json`).
    3.  **[Logical Gap Filled]** If a file is uploaded (PDF/DOCX):
        *   Save the original file in the session directory.
        *   Use a parsing library (`PyMuPDF` for PDF, `python-docx` for DOCX) to extract the full text.
        *   Save the extracted text to a file (e.g., `01_source_document_text.txt`). This raw text is what the LLM will use, not the file itself.
    4.  Return the `session_id` to the client. The UI must store this ID for all subsequent requests.

*   **LLM Task Involved:** None yet. This is purely setup and data ingestion.

---

#### **Phase 2: Analysis & Plan Generation**

The system analyzes the ingested information and proposes a structured plan for the new document.

*   **Trigger:** The UI, having received a `session_id` from Phase 1, immediately calls the planning endpoint.
*   **API Endpoint:** `POST /api/v1/projects/{session_id}/plan`
*   **Backend Actions:**
    1.  Load the initial prompt and any extracted source text from the session directory.
    2.  Synthesize this information into a single, comprehensive prompt for the LLM.
        *   *Example Prompt:* "Based on the user's request '...' and the content of the provided reference document, generate a structured plan (Table of Contents) for a new legal document. The plan should be a JSON object with a 'document_type' and a list of 'sections', each with a unique 'id', a 'title', and a brief 'description' of its purpose."
    3.  Define a Pydantic model for the expected plan structure (e.g., `DocumentPlanModel`).
    4.  Call your `llm_service.invoke_structured()` with the prompt and the `DocumentPlanModel`.
    5.  Save the resulting validated JSON plan to `02_document_plan.json` in the session directory.
    6.  Return the generated plan to the UI for user review.

*   **LLM Task Involved:** **#1. Document Plan Generation**.

---

#### **Phase 3: Plan Review & Approval Loop**

The user has full control to modify the proposed plan before any content is generated.

*   **Trigger:** The user interacts with the plan displayed in the UI.
*   **API Endpoints:**
    *   `PUT /api/v1/projects/{session_id}/plan` (To update the entire plan)
    *   `POST /api/v1/projects/{session_id}/generate` (To approve the plan and kick off generation)
*   **User Interaction & Backend Actions:**
    1.  The UI displays the list of sections from the plan. The user can edit titles, descriptions, re-order sections, add new ones, or delete them.
    2.  Each time the user makes a change, the UI sends the *entire updated plan object* to the `PUT /plan` endpoint. The backend simply overwrites `02_document_plan.json` with the new version. This is simpler and more robust than handling individual micro-updates.
    3.  Once satisfied, the user clicks "Generate Document". This triggers a call to the `/generate` endpoint.

*   **LLM Task Involved:** None. This is a user-centric state management phase.

---

#### **Phase 4: Asynchronous Content Generation & Analysis Pipeline**

This is the most complex phase. Generating a full document can be slow, so it must not block the server or the user.

*   **Trigger:** A request to `POST /api/v1/projects/{session_id}/generate`.
*   **API Endpoint:** `POST /api/v1/projects/{session_id}/generate`
*   **Backend Actions:**
    1.  This endpoint should return an immediate `202 Accepted` response, indicating the job has started.
    2.  **[Logical Gap Filled]** It will launch a **background task** (using FastAPI's `BackgroundTasks` for simplicity, or a more robust system like Celery for production).
    3.  The background task iterates through each section in the approved `02_document_plan.json`.
    4.  For **each section**, it executes a pipeline:
        *   **Step 4a (Generate):** Call the LLM to generate the section's content. **(LLM Task #2)**
        *   **Step 4b (Analyze Risk):** Take the newly generated text and immediately call the LLM again to perform a risk analysis on it. **(LLM Task #4)**
        *   **Step 4c (Extract Entities):** Call the LLM with the generated text to extract named entities. **(LLM Task #5)**
        *   **Step 4d (Extract Deliverables):** Call the LLM with the generated text to extract deliverables. **(LLM Task #6)**
        *   **Step 4e (Save):** Store all of this information in a single, structured JSON file for that section, e.g., `<section_id>.json`. This file will contain the content, its analysis metadata, and a history log.
    5.  The UI will poll a status endpoint (`GET /api/v1/projects/{session_id}/status`) to check the progress of the generation. This endpoint reads the session directory to see how many section files have been created.

*   **LLM Tasks Involved:** **#2, #4, #5, #6**.

---

#### **Phase 5: Iterative Review & Refinement Loop**

The user can now see the fully generated document and interact with it section by section.

*   **Trigger:** User clicks on a section in the UI to edit or uses an AI tool.
*   **API Endpoints:**
    *   `GET /api/v1/projects/{session_id}/document`: Fetches the complete, assembled document content with all metadata for the UI.
    *   `PUT /api/v1/projects/{session_id}/sections/{section_id}`: Updates the content of a section with the user's manual edits.
    *   `POST /api/v1/projects/{session_id}/sections/{section_id}/refine`: Applies an AI tool/service to a section's content.
*   **Backend Actions:**
    1.  **User Manual Edit:** When the user edits text and saves, the UI calls the `PUT /sections/{section_id}` endpoint with the new content.
        *   The backend updates the content in `<section_id>.json`.
        *   **Crucially**, it then **re-runs the analysis pipeline (Steps 4b, 4c, 4d)** on the *new user-provided text* and updates the risk, entity, and deliverable metadata for that section.
    2.  **AI Tool Usage (e.g., Simplify):** When the user selects text and clicks "Simplify", the UI calls the `POST /refine` endpoint.
        *   The request body specifies the action (e.g., `{"action": "simplify"}`).
        *   The backend calls the appropriate LLM task (e.g., **#3. Text Simplification**).
        *   It returns the modified text. The UI can then replace the content in the editor, and the user can choose to save it (which triggers the manual edit workflow above).

*   **LLM Tasks Involved:** **#3, #7, #8, #9, #10** (all the AI tools and refinement tasks).

---

#### **Phase 6: Finalization & Export**

*   **Trigger:** The user is satisfied with the document and clicks "Export".
*   **API Endpoint:** `GET /api/v1/projects/{session_id}/export?format=pdf`
*   **Backend Actions:**
    1.  Assembles the latest version of all section content from the session files.
    2.  Uses a templating engine (like Jinja2) and an HTML-to-PDF library to render the final document based on a design template from your `document_design_resource_path`.
    3.  Returns the final file for the user to download.

This workflow provides a clear, sequential, and robust path from initial idea to final document, handling the complexities of user interaction and long-running AI tasks. We can now proceed to define the Pydantic models and the first set of API endpoints for **Phase 1 and 2**.