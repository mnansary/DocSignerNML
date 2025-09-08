Of course. Let's proceed step-by-step. It's an excellent strategy to solidify one component before moving to the next.

Based on your project description, the user's desired interactions, and the provided API capabilities, here is an exhaustive list of the distinct tasks the LLM will be responsible for. We will treat this as our foundational checklist.

Each task requires a unique combination of system prompts, user inputs, and potentially specific generation parameters from your `config.yaml`.

---

### Exhaustive List of LLM-Centric Tasks

#### Category 1: Document Scaffolding and Core Generation

These tasks are fundamental to creating the initial document structure and content.

1.  **Document Plan Generation**
    *   **Objective:** To convert a high-level user request (e.g., "a freelance graphic design contract") into a structured, logical outline of the document.
    *   **Input to LLM:** A system prompt defining the expected JSON structure, and a user prompt containing the document description.
    *   **Expected LLM Output:** A strictly formatted JSON object containing the `document_type` and a list of `sections`, where each section has an `id`, `title`, and `description`.
    *   **Key Challenge / Prompt Engineering Focus:** Ensuring the LLM *always* returns valid JSON in the specified format. Using `response_format: {"type": "json_object"}` is critical here. The prompt must be very explicit about the required keys and data types.

2.  **Section/Clause Content Generation**
    *   **Objective:** To write the full legal text for a single section based on the approved plan.
    *   **Input to LLM:** A system prompt positioning the LLM as a legal drafter, and a user prompt that includes the overall `document_type`, the specific `section_title`, and the `section_description` for context.
    *   **Expected LLM Output:** A string of well-formatted legal text for that section.
    *   **Key Challenge / Prompt Engineering Focus:** Generating text that is legally sound, coherent, and contextually aware of its place within the larger document.

#### Category 2: Content Analysis and Augmentation (The "AI Tools")

These are the value-add services the user can invoke on existing text.

3.  **Text Simplification (`/api/ml/text/simplify`)**
    *   **Objective:** To translate complex legal jargon into plain, easy-to-understand language.
    *   **Input to LLM:** A system prompt instructing it to act as a legal explainer, and a user prompt containing the block of legal text to be simplified.
    *   **Expected LLM Output:** A string containing the simplified version of the text.
    *   **Key Challenge / Prompt Engineering Focus:** Simplifying the language without losing the core legal meaning or nuance.

4.  **Risk Analysis (`/api/ml/document/analyze-risk`)**
    *   **Objective:** To review a piece of text (or the whole document) and identify potential risks, ambiguities, or unfavorable terms for the user.
    *   **Input to LLM:** A system prompt defining what constitutes a "risk" (e.g., vague obligations, lack of limitations on liability, undefined terms) and the text to be analyzed.
    *   **Expected LLM Output:** A structured response, either as a Markdown list or a JSON object, detailing each identified risk and a brief explanation.
    *   **Key Challenge / Prompt Engineering Focus:** Defining the "persona" for the risk analysis. Is it analyzing from the perspective of the client, the other party, or a neutral observer? The prompt must specify this.

5.  **Key Entity Extraction (`/api/ml/document/extract-entities`)**
    *   **Objective:** To parse the document and pull out key pieces of information into a structured format.
    *   **Input to LLM:** A system prompt explaining the task and defining the desired JSON schema for the entities (e.g., names of parties, effective dates, monetary amounts, addresses).
    *   **Expected LLM Output:** A JSON object populated with the extracted entities.
    *   **Key Challenge / Prompt Engineering Focus:** Creating a robust JSON schema in the prompt that covers all relevant entities and instructing the LLM to return null values for entities it cannot find.

6.  **Deliverable and Obligation Extraction (`/api/ml/task/extract-deliverables`)**
    *   **Objective:** To identify all actionable items, tasks, responsibilities, and deadlines within a contract.
    *   **Input to LLM:** A system prompt instructing the LLM to act as a project manager or compliance officer, and the document text.
    *   **Expected LLM Output:** A structured JSON list where each item represents a deliverable and contains keys like `obligation`, `responsible_party`, `due_date`, and the `source_text`.
    *   **Key Challenge / Prompt Engineering Focus:** Distinguishing between actual obligations and descriptive or recital text.

7.  **Translation (`/api/ml/document/translate`)**
    *   **Objective:** To translate a piece of legal text from one language to another.
    *   **Input to LLM:** A system prompt specifying the role of a professional legal translator and the target language, plus the source text.
    *   **Expected LLM Output:** A string containing the translated text.
    *   **Key Challenge / Prompt Engineering Focus:** Maintaining the precise legal meaning across languages, as literal translations can often be incorrect in a legal context.

8.  **Clause Recommendation (`/api/ml/clause/recommend`)**
    *   **Objective:** Based on the current document context, suggest additional clauses that are commonly included or would be prudent to add.
    *   **Input to LLM:** A system prompt that provides context (e.g., "This is a software development agreement") and asks the LLM to suggest a relevant, missing clause. The input should also include the existing section titles to avoid recommending duplicates.
    *   **Expected LLM Output:** A JSON object with the `recommended_clause_title` and a `reasoning` for why it's recommended.
    *   **Key Challenge / Prompt Engineering Focus:** The LLM needs enough context to make intelligent recommendations rather than generic ones.

#### Category 3: Interactive Refinement and Assistance

These tasks handle the iterative, conversational nature of editing.

9.  **Instruction-Based Text Refinement**
    *   **Objective:** To modify a block of existing text based on a natural language command from the user.
    *   **Input to LLM:** A system prompt setting the context, the *current* text of the clause, and a user instruction like "Make this section more favorable to the client," "Shorten this paragraph," or "Add a provision for a 30-day notice period."
    *   **Expected LLM Output:** A string containing the revised text.
    *   **Key Challenge / Prompt Engineering Focus:** The LLM must accurately interpret the user's intent and perform a targeted edit rather than rewriting the entire section from scratch. This is a "diff" or "edit" task, not a generation task.

10. **Contextual Question Answering**
    *   **Objective:** To answer a user's question about a specific part of the document.
    *   **Input to LLM:** A system prompt telling the LLM to answer questions based *only* on the provided text. The prompt would include the relevant section text and the user's question (e.g., "In this section, what is the deadline for payment?").
    *   **Expected LLM Output:** A direct and concise answer to the question, citing the source text if possible.
    *   **Key Challenge / Prompt Engineering Focus:** Preventing the LLM from hallucinating or using outside knowledge. The prompt must strictly limit its scope to the provided context.

---

We will now proceed with designing and implementing the code to handle these tasks, starting with the configuration and the core LLM service wrappers. Does this list accurately and comprehensively cover the required LLM functionalities for the project?