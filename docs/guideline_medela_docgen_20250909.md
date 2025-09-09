### An Overview of the Document Generation Workflow

#### **Step 1: The Project Kick-off (Getting the Ingredients)**

*   **What the User Does:** The user fills out a simple form. They type in their instructions (the "prompt") and upload a reference PDF. They then click a "Start Building" button.
*   **What the System Does (The "Digital Intern"):** The system acts like an intern starting a new assignment. It creates a brand-new, empty project folder with a unique ID. It then carefully places the user's text prompt into one file and the uploaded PDF into another. Finally, it opens the PDF, reads all the text inside using the `pypdf` library, and saves that raw text into a third file. Now, all the raw materials are neatly organized in one place.
*   **The Goal:** To securely receive and organize all the user's initial materials (instructions and inspiration) into a single, identifiable project workspace.
*   **API Endpoint for this Step:** `POST /api/v1/projects`

---

#### **Step 2: Creating the Blueprint (The Architect's Plan)**

*   **What the User Does:** The user waits for a moment while the system thinks.
*   **What the System Does (The "AI Architect"):** The system now takes the user's instructions and the text from the reference PDF and presents them to the Large Language Model (LLM). It tells the LLM: "You are a senior paralegal. Based on these instructions and this example document, create a logical blueprint or a Table of Contents for the new document. Do not write the full text yet. Just give me the plan." The LLM then returns a structured plan (e.g., Section 1: Introduction, Section 2: Definitions, etc.).
*   **The Goal:** To generate a high-level, structured plan of the document for the user to review and approve *before* any time-consuming content writing begins. This prevents major mistakes and rework.
*   **API Endpoint for this Step:** `POST /api/v1/projects/{project_id}/plan`

---

#### **Step 3: The Supervisor's Review (User Approval)**

*   **What the User Does:** The user sees the blueprint (the Table of Contents) on their screen. They can now act as the supervisor. They can rename sections, delete sections they don't need, or add new ones. Once they are satisfied with the structure, they click a big "Approve Plan & Generate Document" button.
*   **What the System Does:** The system faithfully saves any changes the user makes to the blueprint. When the user clicks the "Approve" button, the system understands this as the final green light to start the main work.
*   **The Goal:** To give the user complete control over the document's structure and to get their explicit approval before committing to the full generation process.
*   **API Endpoints for this Step:**
    *   To save plan changes: `PUT /api/v1/projects/{project_id}/plan`
    *   To approve and start generation: `POST /api/v1/projects/{project_id}/generate`

---

#### **Step 4: The Automated Assembly Line (Content Generation)**

*   **What the User Does:** The user sees a progress indicator on the screen. The system is now in "deep work" mode.
*   **What the System Does (The "AI Writing Team"):** This is an automated, multi-step process that runs in the background. The system goes through the approved blueprint, section by section. For **each section**, it performs a mini-workflow:
    1.  **Drafting:** It tells the LLM: "Write the full legal text for this specific section, keeping the style of the reference document in mind."
    2.  **Analysis:** Once the text is written, it immediately sends it back to the LLM with new instructions: "Now, analyze this text you just wrote for any potential risks," and then again, "Now, extract all key information like names, dates, and amounts from this text."
    3.  **Filing:** It saves the drafted text and all of its analysis (risks, key info) into a dedicated file for that section within the project folder.
    It repeats this for every section in the blueprint until the entire first draft is complete.
*   **The Goal:** To automatically generate the full first draft of the document and simultaneously enrich it with AI-powered analysis and metadata, section by section.
*   **API Endpoint for this Step:** The user will check on progress using `GET /api/v1/projects/{project_id}/status`

---

#### **Step 5: The Editing Room (Collaboration and Refinement)**

*   **What the User Does:** The user can now see and read the complete first draft. They can click on any paragraph to edit it manually, or they can highlight text and use special "AI Assistant" buttons like "Simplify This," "Translate to German," or "Check for Ambiguity."
*   **What the System Does (The "AI Co-pilot"):** If the user edits text manually and saves, the system updates the content and smartly **re-runs the analysis** for just that section to ensure the risk and entity information stays up-to-date. If the user clicks an AI Assistant button, the system sends the selected text to the LLM with that specific command and displays the result. This is a dynamic loop of user edits and AI assistance.
*   **The Goal:** To provide a powerful and interactive editing environment where the user and the AI can collaborate to refine the document to perfection.
*   **API Endpoints for this Step:**
    *   To get the whole document for viewing: `GET /api/v1/projects/{project_id}/document`
    *   To save manual text changes: `PUT /api/v1/projects/{project_id}/sections/{section_id}`
    *   To use an AI tool: `POST /api/v1/projects/{project_id}/sections/{section_id}/assist`

---

#### **Step 6: The Final Product (Printing and Exporting)**

*   **What the User Does:** After all the reviews and edits, the user is happy with the final document. They click "Download PDF."
*   **What the System Does (The "Publisher"):** The system gathers the final version of the text from every section. It pours this content into a professional design template (which might include a company logo). It then generates a clean, polished PDF file and sends it to the user for download.
*   **The Goal:** To deliver a professionally formatted, final document to the user in their desired format.
*   **API Endpoint for this Step:** `GET /api/v1/projects/{project_id}/export?format=pdf`

---

### Input 1: The User Prompt (The "Recipe")

#### **What is it?**
This is a plain text description written by the user. It contains the specific, factual details and instructions for the new document you want to create. It is the "what" and the "who" of your agreement.

#### **What is its Purpose?**
The User Prompt's purpose is to provide the **substance and logic** of the document. The AI reads this to understand the core requirements. It answers the following critical questions:

*   **What type of document is this?** (e.g., Non-Disclosure Agreement, Freelance Contract, Rental Agreement).
*   **Who are the parties involved?** (e.g., "Company ABC, Inc." and "John Smith").
*   **What are the key terms?** (e.g., The project cost is $10,000, the duration is 6 months, the rent is $1,500 per month).
*   **Are there any special conditions?** (e.g., "The confidentiality must last for 5 years," "The freelancer is not allowed to work for competitors," "No pets are allowed in the rental property").

Essentially, the prompt provides the unique, specific details that make this document different from any other.

---

#### **Examples of a GOOD User Prompt:**

A good prompt is clear, specific, and contains the essential facts.

> **Good Example 1 (Specific):**
> "Create a freelance graphic design contract between 'Pixel Perfect Designs LLC' (the Client) and 'Jane Doe' (the Designer). The project is to design a new company logo. The total fee is $2,500, paid 50% upfront and 50% on completion. The deadline for the final logo is November 15, 2025. The client will own all rights to the final artwork."

> **Good Example 2 (Clear):**
> "I need a simple Non-Disclosure Agreement (NDA). The 'Disclosing Party' is 'Innovate Corp' and the 'Receiving Party' is 'Venture Partners LLC'. It should be a mutual NDA, meaning both sides are sharing confidential information. The purpose is to discuss a potential investment. The confidential information includes financial projections and business plans. The term of confidentiality should be 3 years."

#### **Examples of a BAD User Prompt:**

A bad prompt is vague, ambiguous, or misses critical information.

> **Bad Example 1 (Too Vague):**
> "I need a contract."  *(What kind? Between whom? For what?)*

> **Bad Example 2 (Missing Key Info):**
> "An agreement between me and my client for a project." *(What are your names? What is the project? What is the payment?)*

---

### Input 2: The Reference PDF (The "Inspiration Picture")

#### **What is it?**
This is an existing, **digital-native** PDF document that the user uploads. A "digital-native" PDF is one created by a word processor (like Word or Google Docs) where the text can be selected, copied, and pasted. **It cannot be a scanned image of a paper document.**

#### **What is its Purpose?**
The Reference PDF's purpose is to provide **style, structure, and tone**. The AI does **not** copy the specific details (like names or dates) from this document. Instead, it analyzes it to learn:

*   **Structure:** How is a document like this typically organized? What are the standard section headings (e.g., "Recitals," "Term and Termination," "Governing Law")? This helps the AI create a professional and logical blueprint.
*   **Tone & Formality:** Is the language very dense and full of "legalese," or is it more modern and straightforward? The AI will try to match this tone in the new document it generates.
*   **Phrasing:** What kind of standard legal phrases or "boilerplate" language is used? The AI learns the conventional way to phrase common clauses, making the output sound more authentic.

---

#### **What Makes a GOOD Reference PDF?**

*   **It is Text-Based:** You can click and drag your mouse to highlight the text inside it. If you can't, it's a scanned image, and the system cannot read it.
*   **It is Relevant:** If you want to create an NDA, upload another NDA. If you want a rental agreement, upload a rental agreement. This gives the AI the most relevant inspiration.
*   **It is Well-Formatted:** A clean, professional document will give the AI a better "education" than a messy, poorly organized one.

#### **What Makes a BAD Reference PDF?**

*   **It is a Scanned Image:** This is the most common mistake. The `pypdf` library can only read text characters, not pixels in an image. To the system, a scanned PDF is just a blank page.
*   **It is Irrelevant:** Using a Last Will and Testament to inspire a software development contract will confuse the AI and lead to a poorly structured document.
*   **It is Corrupted or Unreadable:** If the text is garbled in the PDF, it will be garbled for the AI.

### Summary: How They Work Together

| Input | Analogy | Purpose |
| :--- | :--- | :--- |
| **User Prompt** | The **Recipe** | Provides the specific **SUBSTANCE** (names, dates, amounts, rules). |
| **Reference PDF** | The **Inspiration Picture** | Provides the **STYLE** (structure, tone, phrasing, format). |

The system intelligently combines these two inputs. It takes the specific instructions from the **prompt** and pours them into the structural and stylistic framework it learned from the **PDF**. This two-part approach ensures the final document is both factually correct for the user's specific situation and professionally formatted like a real legal document.


---
### Step 1: The Project Kick-off (Receiving and Organizing the Raw Materials)

#### **High-Level Goal**

The *only* goal of this step is to securely receive the user's two inputs (the prompt and the reference PDF), create a dedicated, private workspace for their project on the server, and organize the inputs neatly within that workspace. We are not doing any AI work yet; we are simply setting the table.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **The Form:** The user sees a simple web page with two input fields:
    *   A large text box labeled "Describe your document".
    *   A file upload button labeled "Upload Reference PDF".

2.  **User Action:** The user types their detailed instructions into the text box and selects a PDF file from their computer.

3.  **The "Go" Button:** The user clicks a button, let's call it **"Create Project"**.

When this button is clicked, the web browser bundles the text from the text box and the selected PDF file together into a single package and sends it to our server.

---

### 2. The API Call (The Message Sent to the Server)

The browser sends a message to a specific address on our server. This is our first API endpoint.

*   **Endpoint Name:** `POST /api/v1/projects`
    *   **`POST`:** We use `POST` because the user is *creating* a new resource on our server (a new document project).
    *   **`/api/v1/projects`:** This is a clear, logical address. It says we are interacting with version 1 of our API, specifically the "projects" section.

*   **The Payload:** The message contains two parts, sent together as `multipart/form-data` (the standard way to send text and files at the same time):
    1.  **`prompt`:** The text the user wrote.
    2.  **`file`:** The PDF document itself.

---

### 3. The Backend's Job (The Server's To-Do List)

When our FastAPI server receives this message at `/api/v1/projects`, it triggers a function that performs the following actions in a strict sequence:

**Action 1: Create a Unique Project Workspace**
*   The server generates a unique identifier, like a random string of characters (a UUID is perfect for this, e.g., `c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d`). This is the `project_id`.
*   It then creates a new folder inside your pre-configured temporary data directory. The folder name *is* the `project_id`.
    *   **Example Path:** `/home/ansary/work/apsis/DocSignerNML/resources/tmp_data_store/c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d/`
*   This ensures that every project is isolated and there's no chance of mixing up files between different users or documents.

**Action 2: Save the User's Prompt**
*   The server takes the text from the `prompt` part of the payload.
*   It saves this text into a file inside the new project folder. We'll use a structured name and format for consistency.
    *   **Filename:** `00_user_prompt.json`
    *   **Content:** `{"prompt": "Create a freelance graphic design contract between..."}`
    *   *Why JSON?* It's good practice. It allows us to easily add more metadata later if we need to.

**Action 3: Save the Original Reference PDF**
*   The server takes the PDF file from the `file` part of the payload.
*   It saves this PDF directly into the project folder, exactly as it was received.
    *   **Filename:** `01_reference_document.pdf`
    *   *Why save the original?* For auditing, debugging, and potential future features. It's the "source of truth."

**Action 4: Extract Text from the PDF using `pypdf`**
*   This is the most technical part of Step 1. The server now works with the PDF it just saved.
*   It uses the `pypdf` library to perform a text extraction process:
    1.  Initialize an empty string variable, e.g., `extracted_text = ""`.
    2.  Open the PDF file (`01_reference_document.pdf`).
    3.  Create a `PdfReader` object from the file.
    4.  Loop through every page in the PDF document.
    5.  For each page, call the `extract_text()` method.
    6.  Append the text from that page to our `extracted_text` variable, adding a newline character to separate pages.
*   **Crucial Error Handling:** The code must check if the extracted text is empty or just whitespace. If it is, this means the PDF was likely a **scanned image**. In this case, the process should stop and return an error to the user, telling them to upload a text-based PDF.

**Action 5: Save the Extracted Text**
*   The server takes the complete `extracted_text` string.
*   It saves this plain text into a new file inside the project folder.
    *   **Filename:** `02_extracted_text.txt`
    *   *Why a separate file?* This is the clean, usable text that our AI will actually read in the next step. It separates the "source" (the PDF) from the "workable material" (the .txt file).

**Action 6: Send a Confirmation to the User**
*   After all the files have been saved and the text has been successfully extracted, the server's job for this step is done.
*   It sends a response back to the user's browser. The response is a simple JSON object containing the unique ID for the newly created project.
    *   **Response Body:** `{"project_id": "c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d"}`
*   The user's browser receives this `project_id` and must store it. It will act like a "library card" or a "ticket number" to identify this specific project in all future API calls.

---

### The Final Result of Step 1

The user sees a "Success!" message and is moved to the next screen. On the server, the project folder now looks like this:

```
/resources/tmp_data_store/
└── c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d/
    ├── 00_user_prompt.json
    ├── 01_reference_document.pdf
    └── 02_extracted_text.txt
```

All the ingredients are now perfectly prepped and organized, ready for the AI Architect in Step 2.

---

### Step 2: Creating the Blueprint (The AI Architect's Plan)

#### **High-Level Goal**

The purpose of this step is to transform the user's raw inputs (the prompt and the reference text) into a structured, high-level plan for the new document. We are **not** writing the full legal text yet. We are creating a "Table of Contents on steroids"—a logical outline that the user can review and approve. This prevents the AI from wasting time writing a document the user doesn't want.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **Automatic Trigger:** This step begins *immediately* after Step 1 successfully completes. The browser receives the `project_id` and, without the user needing to click anything else, it automatically makes a new request to the server to start the planning phase.
2.  **Waiting for the "Architect":** The user's screen changes. They now see a loading indicator with a message like: "Analyzing your documents and creating a plan..." or "Designing your document structure..." This lets them know that the AI is working.

---

### 2. The API Call (The Message Sent to the Server)

The browser, using the `project_id` it received from Step 1, sends a new message to the server.

*   **Endpoint Name:** `POST /api/v1/projects/{project_id}/plan`
    *   **`POST`:** We are still using `POST` because we are *creating* a new resource: the plan itself.
    *   **`/api/v1/projects/{project_id}/plan`:** This address is very specific. It says, "For the project with *this specific ID*, I want you to create a *plan*." The `{project_id}` part will be replaced with the actual ID, e.g., `c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d`.

*   **The Payload:** This request has **no body or payload**. All the information the server needs is already sitting in the project folder on the server. The `project_id` in the URL is the only key the server needs to find the right materials.

---

### 3. The Backend's Job (The Server's To-Do List)

When the FastAPI server receives this request, it performs a critical sequence of intelligent actions.

**Action 1: Locate and Read the Project Materials**
*   The server uses the `project_id` from the URL to find the correct project folder.
*   It opens and reads the contents of two files:
    1.  `00_user_prompt.json` (to get the user's specific instructions).
    2.  `02_extracted_text.txt` (to get the content from the reference PDF for style and structure).

**Action 2: Craft the Master Prompt for the LLM (Prompt Engineering)**
*   This is the most important part of Step 2. The server acts as a "prompt engineer," combining the information it just read into a single, highly detailed instruction for the LLM. This is **not** just sending the raw text. The prompt is carefully constructed.
*   **The Structure of the Master Prompt:**
    ```
    You are an expert legal assistant specializing in document structuring. Your task is to create a comprehensive plan or a Table of Contents for a new legal document based on the user's requirements and a reference document.

    --- USER'S REQUIREMENTS ---
    [The server inserts the text from 00_user_prompt.json here]

    --- REFERENCE DOCUMENT TEXT (for style and structure inspiration) ---
    [The server inserts the text from 02_extracted_text.txt here]

    --- YOUR INSTRUCTIONS ---
    Analyze all the information above and generate a structured plan. You MUST respond with a single, valid JSON object and nothing else.
    The JSON object must have a key named "document_type" (a string) and a key named "sections" (a list of objects).
    Each object in the "sections" list must have exactly three keys:
    1. "id": a short, unique, lowercase identifier (e.g., "introduction", "confidentiality_clause").
    2. "title": a clean, human-readable title for the section (e.g., "Introduction", "Confidentiality Clause").
    3. "description": a one-sentence explanation of what this section will cover.
    ```

**Action 3: Define the Expected JSON Structure in Code**
*   To ensure the LLM's response is reliable, the backend code defines Pydantic models that perfectly match the requested JSON structure. This allows for automatic validation.
    ```python
    # In your code (e.g., a models.py file)
    from pydantic import BaseModel, Field
    from typing import List

    class SectionPlan(BaseModel):
        id: str = Field(..., description="A unique lowercase identifier.")
        title: str = Field(..., description="The human-readable section title.")
        description: str = Field(..., description="A brief description of the section's purpose.")

    class DocumentPlan(BaseModel):
        document_type: str = Field(..., description="The type of the legal document.")
        sections: List[SectionPlan]
    ```

**Action 4: Call the LLM and Validate the Response**
*   The server now calls your `LLMService`.
*   It uses the `invoke_structured()` method, which is perfect for this task.
*   It passes two arguments:
    1.  The big "Master Prompt" it just crafted.
    2.  The `DocumentPlan` Pydantic model as the `response_model`.
*   The `invoke_structured` function sends the prompt to the LLM, gets the JSON response, and automatically checks if it matches the `DocumentPlan` structure. If it doesn't, it will raise an error, which we can handle gracefully.

**Action 5: Save the Validated Plan**
*   Once the LLM returns a valid plan that passes Pydantic validation, the server saves this new piece of information.
*   It creates a new file in the project folder.
    *   **Filename:** `03_document_plan.json`
    *   **Content:** The clean JSON blueprint generated by the AI.

**Action 6: Send the Plan Back to the User**
*   Finally, the server sends the validated JSON plan back to the user's browser as the successful response to the API call.

---

### The Final Result of Step 2

*   **On the Server:** The project folder is now more complete.
    ```
    /resources/tmp_data_store/
    └── c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d/
        ├── 00_user_prompt.json
        ├── 01_reference_document.pdf
        ├── 02_extracted_text.txt
        └── 03_document_plan.json  <-- NEW FILE
    ```

*   **In the Browser:** The loading indicator disappears. The user now sees the AI-generated plan displayed as a clean, easy-to-read list. Each item in the list shows the section title (e.g., "Confidentiality Obligations") and its short description. This is the blueprint they will review in Step 3.


--- 

### Step 3: The Supervisor's Review (User Approval and Final Go-Ahead)

#### **High-Level Goal**

This step has two main goals:
1.  To give the user **complete and easy control** to modify the AI-generated plan to their exact specifications.
2.  To get the user's **explicit approval** on the final structure before a single word of the full document is written. This is the final "point of no return" before the heavy lifting of content generation begins.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **Viewing the Plan:** The user sees the plan that was generated in Step 2. It's displayed as an interactive list. Each item in the list represents a section of the future document.

2.  **Interactive Controls:** Next to each section title, or perhaps through a simple drag-and-drop interface, the user has several options:
    *   **Edit:** They can click to change the `title` or `description` of any section.
    *   **Re-order:** They can drag sections up or down to change the document's flow.
    *   **Delete:** They can remove a section they feel is unnecessary.
    *   **Add:** There is a button, "Add New Section," which lets them create a new, blank section in the plan.

3.  **The Two Key Buttons:** After making their changes, the user has two main action buttons at the bottom of the screen:
    *   **`Save Plan`:** A non-finalizing button. The user can click this at any time to save their changes without starting the document generation. The UI will send the updated plan to the server.
    *   **`Approve & Generate Document`:** This is the big, green-light button. Clicking this tells the system, "The plan is perfect. Proceed with writing the content."

---

### 2. The API Calls (The Messages Sent to the Server)

This step involves two distinct API endpoints corresponding to the two main user actions.

#### **Endpoint A: Saving Plan Modifications**

*   **Endpoint Name:** `PUT /api/v1/projects/{project_id}/plan`
    *   **`PUT`:** We use `PUT` because it semantically means "replace the existing resource with this new version." The user is providing the *entire*, updated version of the plan to replace the old one.
    *   **`/api/v1/projects/{project_id}/plan`:** The address is the same as the one we used to *get* the plan, but the method (`PUT`) is different, indicating a different action.

*   **The Payload:** The browser sends the **complete, modified plan object** in the body of the request. It doesn't just send the one change; it sends the whole thing to ensure the server always has the latest full version.
    *   **Example Body:** `{"document_type": "...", "sections": [{"id": "...", "title": "New Edited Title", ...}, ...]}`

#### **Endpoint B: Approving the Plan and Starting Generation**

*   **Endpoint Name:** `POST /api/v1/projects/{project_id}/generate`
    *   **`POST`:** We use `POST` here to signify that we are initiating a new *process* or *job*—the generation task.
    *   **`/api/v1/projects/{project_id}/generate`:** A clear, action-oriented endpoint name.

*   **The Payload:** This request needs **no payload**. The server will work off the latest saved version of the plan in the project folder.

---

### 3. The Backend's Job (The Server's To-Do List)

The server's responsibilities are split based on which endpoint is called.

#### **Handling the `PUT /plan` Request (Saving Changes):**

1.  **Validation:** The server receives the new plan object in the request body. It should immediately validate this object against its `DocumentPlan` Pydantic model to ensure the structure is still correct (e.g., the user didn't delete a required key).
2.  **Overwrite:** If the new plan is valid, the server simply overwrites the `03_document_plan.json` file in the project folder with the new data. This is an atomic and simple operation.
3.  **Confirmation:** The server sends back a success response, like `{"status": "Plan updated successfully"}`.

#### **Handling the `POST /generate` Request (The Green Light):**

1.  **Acknowledge Immediately:** This is the most important part of the logic. The full generation process in Step 4 will take a significant amount of time (from seconds to minutes). We cannot make the user wait for it to finish. Therefore, this endpoint must respond **immediately**.
2.  **Launch Background Task:** The server launches the entire Step 4 workflow as a **background task**. In FastAPI, this is easily done using the `BackgroundTasks` feature. This frees up the server to send a quick response while the real work begins separately.
3.  **Send "Accepted" Response:** The server immediately returns a `202 Accepted` HTTP status code. This code tells the browser, "I have received and understood your request, and I have started the process. The job is now running in the background."
    *   **Response Body:** `{"status": "Generation process started", "project_id": "..."}`

---

### The Final Result of Step 3

*   **On the Server:** The project folder now contains the final, user-approved version of the plan.
    ```
    /resources/tmp_data_store/
    └── c7a4e5d8-2b8f-4a0e-8c5d-9e6b3a1f9c0d/
        ├── ... (previous files)
        └── 03_document_plan.json  <-- FINAL, USER-APPROVED VERSION
    ```
    A new background process has been kicked off, which will start creating new files as it runs through Step 4.

*   **In the Browser:** The user's screen changes again. The interactive plan view is replaced by a progress tracking screen. It might show a message like, "Generating your document... Section 1 of 10 complete." The browser will now periodically "ping" the server (using a new "status" endpoint we will define for Step 4) to get updates on the generation progress.

---

### Step 4: The Automated Assembly Line (Content Generation & Analysis)

#### **High-Level Goal**

The goal of this step is to take the user-approved plan and methodically generate the full text for **every section**. Crucially, it doesn't just write the text; it immediately runs a multi-point AI analysis on that new text to enrich it with valuable metadata (risks, key entities, etc.). This is a fully automated, background process.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **The Progress View:** The moment the user clicks "Approve & Generate Document" in Step 3, their screen changes to a progress or status view. They are now passive observers.
2.  **Real-time Updates:** This view is not static. It shows the generation process as it happens, giving the user a sense of progress and transparency. It might look like a checklist:
    *   **Document Generation in Progress...**
    *   `[✓]` Section 1: Introduction - *Complete*
    *   `[✓]` Section 2: Definitions - *Complete*
    *   `[⚙️]` Section 3: Confidentiality Obligations - *Generating...*
    *   `[ ]` Section 4: Term and Termination - *Queued*
3.  **Polling for Status:** To achieve this, the browser's JavaScript will now "poll" the server every few seconds. It repeatedly calls a special "status" endpoint to ask, "What's the latest progress?" and updates the checklist accordingly.
4.  **Completion:** Once all sections are complete, the progress view will automatically disappear and be replaced by the full document editor view (the start of Step 5).

---

### 2. The API Call (The Communication During Generation)

Only one new endpoint is needed for this phase, and it's used exclusively for progress updates.

*   **Endpoint Name:** `GET /api/v1/projects/{project_id}/status`
    *   **`GET`:** We use `GET` because the browser is simply retrieving (`GET`ting) the current state of the project.
    *   **`/api/v1/projects/{project_id}/status`:** A clear, descriptive address for checking the status of a specific project.

*   **The Response:** When the browser calls this endpoint, the server quickly checks the project folder and returns a JSON object summarizing the progress.
    *   **Example Response:**
        ```json
        {
          "project_id": "c7a45d8...",
          "status": "in_progress",
          "total_sections": 10,
          "completed_sections": 3,
          "progress_details": [
            {"title": "Introduction", "status": "complete"},
            {"title": "Definitions", "status": "complete"},
            {"title": "Confidentiality Obligations", "status": "in_progress"}
          ]
        }
        ```

---

### 3. The Backend's Job (The Background Task's Detailed Workflow)

This is the core logic that was launched as a background task at the end of Step 3. It's a systematic loop.

**Action 1: Initialize the Process**
*   The background task starts.
*   It locates the project folder using the `project_id`.
*   It opens and reads the final, approved `03_document_plan.json` file to get its list of jobs (the sections).

**Action 2: Loop Through Each Section**
*   The task begins a `for` loop, iterating through each section object in the `sections` list from the plan. For each section, it executes the following "pipeline":

**Action 2a: The "Drafting Station" - Generate Section Content**
*   **Prompt Engineering:** It crafts a highly specific prompt for the LLM to generate the content.
    *   **Example Prompt:** "You are a legal drafting expert. For a document titled 'Mutual Non-Disclosure Agreement', write the full and complete legal text for the section called 'Confidentiality Obligations'. This section should cover the definition of confidential information and the responsibilities of the receiving party."
*   **LLM Call:** It calls `llm_service.invoke()` with this prompt. It expects a single string of legal text as the output.

**Action 2b: The "Inspection Station" - Analyze Risks**
*   **Prompt Engineering:** It takes the text generated in the previous step and uses it in a *new* prompt.
    *   **Example Prompt:** "You are a risk analysis expert. Review the following legal clause and identify any potential risks, ambiguities, or unfavorable terms. Respond with a JSON object containing a list of identified risks."
*   **LLM Call:** It calls `llm_service.invoke_structured()`, passing this prompt and a Pydantic model designed to capture a list of risks.

**Action 2c: The "Tagging Station" - Extract Entities**
*   **Prompt Engineering:** It uses the same generated text again in a third prompt.
    *   **Example Prompt:** "You are a data extraction bot. Parse the following text and extract key entities like party names, dates, locations, and monetary amounts. Respond with a JSON object mapping entity types to their values."
*   **LLM Call:** It calls `llm_service.invoke_structured()` with this prompt and a Pydantic model for entities.

**Action 2d: The "Filing Station" - Save All Results**
*   The task now has all the pieces for the current section: the text, the risk analysis, and the extracted entities.
*   It creates a **new file** in the project folder. The filename is based on the section's `id` from the plan (e.g., `confidentiality_obligations.json`).
*   **File Content:** This JSON file is a structured container for everything related to this section.
    ```json
    {
      "section_id": "confidentiality_obligations",
      "title": "Confidentiality Obligations",
      "content_history": [
        {
          "version": 1,
          "timestamp": "2025-09-08T10:00:00Z",
          "author": "ai_generation",
          "content": "The full legal text generated by the LLM..."
        }
      ],
      "analysis": {
        "risks": [
          {"risk": "The definition of 'Confidential Information' is too broad.", "severity": "medium"}
        ],
        "entities": [
          {"type": "Party", "value": "Disclosing Party"}
        ]
      }
    }
    ```
    *(Note: Using a `content_history` array is forward-thinking for the editing in Step 5).*

**Action 3: Repeat**
*   The loop continues to the next section in the plan and repeats the entire pipeline (Draft -> Inspect -> Tag -> File) until all sections have been processed.

**Action 4: Finalize**
*   Once the loop is finished, the background task's job is complete. It might update a final status file in the project directory to mark the project as `"status": "complete"`.

---

### The Final Result of Step 4

*   **On the Server:** The project folder is now richly populated with detailed files, one for each section of the document.
    ```
    /resources/tmp_data_store/
    └── c7a45d8.../
        ├── ... (previous files 00 to 03)
        ├── introduction.json
        ├── definitions.json
        ├── confidentiality_obligations.json
        └── ... (and so on for every section)
    ```

*   **In the Browser:** The polling from the `GET /status` endpoint now returns a "complete" status. The progress view disappears, and the browser automatically loads the main editor interface, signaling the beginning of Step 5. The user is presented with the full first draft of their document for the very first time.

--- 

### Step 5: The Editing Room (Iterative Refinement)

#### **High-Level Goal**

The goal of this step is to provide the user with a powerful and intuitive interface to review, edit, and enhance the AI-generated draft until it is perfect. This is not a single action but a continuous *loop* of actions. The user can make manual changes, request AI assistance, and see the document and its analysis update in real time.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **The Two-Panel Workspace:** The user is presented with a sophisticated editor, typically split into two main panels:
    *   **Left Panel (The Document Editor):** This shows the full, assembled text of the document. It looks and feels like a standard word processor. The user can click anywhere, type, delete, and edit text freely.
    *   **Right Panel (The Analysis & AI Co-pilot):** This panel is contextual. When the user's cursor is inside a specific section in the left panel, this right panel automatically updates to show the AI's analysis (risks, extracted entities) for *that specific section*. It also contains a bank of "AI Co-pilot" buttons.

2.  **User Actions in the Loop:** The user can now perform a variety of actions, as many times as they need:
    *   **Manual Editing:** They read a sentence and decide to rephrase it. They simply type the changes. An "Auto-Save" feature or a "Save Changes" button appears, indicating the document needs to be updated.
    *   **Using the AI Co-pilot:** They highlight a complex paragraph and click an action button in the right panel, such as:
        *   `[Simplify Text]`
        *   `[Translate to German]`
        *   `[Check for Risks]`
        *   `[Suggest an Alternative Clause]`
    *   The system processes this request and shows the result, which the user can then accept to replace the original text.

---

### 2. The API Calls (The Communication in the Loop)

This interactive phase requires three distinct endpoints to function smoothly.

#### **Endpoint A: Loading the Document for Editing**

*   **Endpoint Name:** `GET /api/v1/projects/{project_id}/document`
*   **Purpose:** Called once when the editor first loads. It fetches the entire drafted document with all its metadata.
*   **How it Works:** The browser requests the full document. The server assembles the latest content and analysis from all the individual section files and sends it back as one large JSON object.

#### **Endpoint B: Saving Manual Edits**

*   **Endpoint Name:** `PUT /api/v1/projects/{project_id}/sections/{section_id}`
*   **Purpose:** Called every time the user saves a change to a specific section.
*   **Payload:** The request body contains the *entire new text* of the section the user just edited. `{"content": "This is the new, user-modified text of the section..."}`.

#### **Endpoint C: Using an AI Co-pilot Tool**

*   **Endpoint Name:** `POST /api/v1/projects/{project_id}/sections/{section_id}/assist`
*   **Purpose:** Called when the user clicks any of the AI Co-pilot buttons.
*   **Payload:** The request body specifies which action to perform and the text to perform it on. `{"action": "simplify", "text": "The user-highlighted complex legal text..."}`.

---

### 3. The Backend's Job (Handling the Interactive Loop)

The server's logic is now designed to handle these short, frequent requests.

#### **Handling `PUT /sections/{section_id}` (Saving Manual Edits):**

This is a critical workflow that ensures the document's intelligence stays up-to-date.

1.  **Locate & Load:** The server finds the correct project folder and loads the relevant section file (e.g., `confidentiality_obligations.json`).
2.  **Update History:** It takes the new user-provided content from the request. It adds a new entry to the `content_history` array in the JSON file, marking the `author` as `"user_edit"` and adding a new timestamp. This creates an audit trail.
3.  **TRIGGER THE ANALYSIS PIPELINE (RE-ANALYSIS):** This is the key. The server now treats the user's new text as a fresh piece of content. It **re-runs the analysis pipeline from Step 4** on this new text:
    *   It calls the LLM to analyze risks.
    *   It calls the LLM to extract entities.
4.  **Update Analysis:** It completely replaces the old `analysis` object in the JSON file with the brand-new results from the re-analysis.
5.  **Save & Respond:** It saves the updated section file and sends the *new analysis data* back to the browser. This allows the right-hand "Analysis Panel" in the UI to refresh instantly with information relevant to the user's latest changes.

#### **Handling `POST /assist` (Using an AI Tool):**

This workflow is simpler because it doesn't save anything directly; it just provides a transformation.

1.  **Identify Action:** The server looks at the `action` field in the request body (e.g., "simplify").
2.  **Prompt Engineering:** It crafts the correct prompt for the requested task.
    *   If `action` is "simplify": "You are a helpful assistant. Simplify the following legal text into plain English: [user's text]".
    *   If `action` is "translate": "You are a professional translator. Translate the following text to German: [user's text]".
3.  **LLM Call:** It calls the `llm_service.invoke()` method with the crafted prompt.
4.  **Respond with Result:** The server takes the LLM's text output and sends it back to the browser.
    *   **Response:** `{"result": "This is the simplified version of the text."}`
5.  The browser then displays this `result` to the user, who can choose to accept it. If they do, the new text is placed in the editor, and the "Save Changes" (`PUT`) workflow is triggered.

---

### The Final Result of Step 5

*   **On the Server:** The project folder's section files (`*.json`) are now mature. Their `content_history` may show multiple versions from both the AI and the user. The `analysis` object within each file is always perfectly synchronized with the *very latest* version of the content.

*   **In the Browser:** The user has reviewed and refined the entire document. They are fully satisfied with the text. The document is now considered final and is ready to be formatted and exported in the last step.

---

### Step 6: The Final Product (Formatting and Exporting)

#### **High-Level Goal**

The single goal of this step is to take the final, approved content from the project and render it into a professionally formatted document (like a PDF) that the user can download, share, or print. This is the "publishing" phase.

---

### 1. The User's Experience (What Happens in the Browser)

1.  **The "Export" Button:** The user, satisfied with the content in the editor, looks for a final action button. This button is clearly labeled **"Download PDF"** or **"Export"**.
2.  **User Action:** The user clicks this button.
3.  **File Download:** After a brief moment of processing, their browser's standard "Save File" dialog box appears, prompting them to save a file named something like `non-disclosure-agreement.pdf` to their computer. The process is now complete from their perspective.

---

### 2. The API Call (The Message Sent to the Server)

The browser sends a final request to the server to generate the document.

*   **Endpoint Name:** `GET /api/v1/projects/{project_id}/export`
    *   **`GET`:** We use `GET` because the user is *retrieving* the final representation of the project resource.
    *   **`/api/v1/projects/{project_id}/export`:** A clear endpoint that signifies the user wants to export the final artifact of a specific project.
*   **Query Parameters:** To allow for future flexibility (e.g., exporting as DOCX), the desired format is specified as a query parameter in the URL.
    *   **Example URL:** `/api/v1/projects/c7a45d8.../export?format=pdf`
*   **The Payload:** There is no request body. All necessary information is on the server.

---

### 3. The Backend's Job (The Server's Publishing Workflow)

When the server receives this request, it executes a linear, multi-stage pipeline to build the final document.

**Action 1: Assemble the Final Content**
*   The server locates the correct project folder using the `project_id`.
*   It creates an empty list or dictionary in memory to hold the assembled document.
*   It refers to the `03_document_plan.json` file to get the correct order of the sections.
*   It then loops through the sections in that order. For each section `id`, it opens the corresponding file (e.g., `introduction.json`, `definitions.json`).
*   From each section file, it extracts only the **latest version of the content** from the `content_history` array.
*   It assembles this data into a structured object ready for rendering.
    *   **Example Data Object:**
        ```python
        document_data = {
            "title": "Mutual Non-Disclosure Agreement",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "The latest text of the introduction..."
                },
                {
                    "title": "Definitions",
                    "content": "The final version of the definitions section..."
                }
                # ...and so on
            ]
        }
        ```

**Action 2: Select and Load the Design Template**
*   The server looks at the `document_design_resource_path` from your `config.yaml`.
*   Within that directory, it selects an appropriate HTML template. For now, we can have a `default_legal_template.html`. In the future, you could have different templates for different document types.
*   This template is a standard HTML file but with placeholders for our data, using a templating language like Jinja2.
    *   **Example Template Snippet (`default_legal_template.html`):**
        ```html
        <h1>{{ document.title }}</h1>
        {% for section in document.sections %}
            <h2>{{ section.title }}</h2>
            <p>{{ section.content | replace('\n', '<br>') }}</p>
        {% endfor %}
        ```
        *(Note the filter to convert newline characters into HTML line breaks for proper formatting.)*

**Action 3: Render the HTML**
*   The server uses the Jinja2 library to merge the `document_data` object (from Action 1) with the `default_legal_template.html` (from Action 2).
*   The output of this step is a single string containing the complete, final HTML of the document, with all the content correctly placed.

**Action 4: Convert HTML to PDF**
*   This is the final transformation step. The server uses a library designed for HTML-to-PDF conversion. (Popular choices in Python include WeasyPrint or using a headless browser via libraries like Playwright).
*   It feeds the HTML string from Action 3 into this conversion library.
*   The library processes the HTML and CSS and outputs the final document as a binary PDF object in memory.

**Action 5: Send the File to the User**
*   The server constructs a final HTTP response.
*   Instead of sending JSON (like in previous steps), it uses FastAPI's `StreamingResponse` or `Response`.
*   It sets the `Content-Type` header to `application/pdf`.
*   It sets the `Content-Disposition` header to tell the browser this is an attachment that should be downloaded, and suggests a filename (e.g., `attachment; filename="document.pdf"`).
*   It sends the binary PDF data as the body of the response.
*   The browser receives this response and, because of the headers, it knows to trigger a file download instead of trying to display it on the page.

---

### The Final Result of Step 6

*   **On the Server:** No new files are permanently saved in the project folder. The PDF is generated on-the-fly and streamed directly to the user. The project folder remains as a complete data record of the document's creation.
*   **In the Browser:** The user has a polished, professional PDF file saved to their local computer.

The entire workflow, from a vague idea and an inspiration file to a finished, downloadable document, is now complete.