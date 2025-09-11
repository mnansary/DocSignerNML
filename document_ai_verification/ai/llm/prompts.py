import json
# document_ai_verification/ai/llm/prompts.py

# This first prompt is still needed for the initial analysis of the NSV text.
def get_ns_document_analysis_prompt(page_text_content: str) -> str:
    """
    Generates a prompt to instruct an LLM to analyze the text of a
    non-signed document page and identify all required user inputs.
    """
    prompt = f"""
    **Your Role:** You are a hyper-attentive, detail-oriented document processing specialist with extensive experience in form analysis and data extraction. Your expertise lies in meticulously reviewing textual content from various documents, such as legal forms, applications, contracts, and administrative paperwork, to pinpoint every instance where a user must provide personal input. You approach this task with precision, ensuring no potential input field is overlooked, while strictly adhering to predefined guidelines to maintain consistency and accuracy.

    **Your Task:** Carefully examine the provided text from a single page of a non-signed document. Your objective is to identify and catalog all locations where the document explicitly or implicitly requires a user to enter information, such as writing text, signing, dating, initialing, checking boxes, or providing other details. This analysis is crucial for automating document preparation processes, so your output must be thorough, reliable, and formatted exactly as specified.

    **Critical Instructions:**
    1. **Identify the Marker Text:** For each input field, locate and extract the exact, unique, machine-printed text label or phrase that is immediately adjacent to or directly associated with the field. This "marker_text" serves as a reliable anchor for later verification and must be copied verbatim from the document text without any alterations, paraphrasing, or summarization. For example:
       - Correct: "Signature of Applicant:"
       - Incorrect: "applicant's signature" (this is paraphrased and lacks the original punctuation and capitalization).
       Focus on text that clearly indicates an input is needed, such as labels ending with colons, underscores, or blank lines described in the text.

    2. **Determine the Input Type:** Classify each identified input field into one of the following predefined categories based on the context and marker text:
       - 'signature': For fields requiring a handwritten or electronic signature (e.g., "Signature:", "Sign Here:").
       - 'date': For fields requiring a date entry (e.g., "Date:", "Date of Birth:").
       - 'full_name': For fields requiring the user's full printed name (e.g., "Print Name:", "Full Name:").
       - 'initials': For fields requiring initials (e.g., "Initial Here:", "Applicant's Initials:").
       - 'checkbox': For fields involving checking or marking a box (e.g., "Check if Applicable □", "Yes/No □").
       - 'address': For fields requiring an address (e.g., "Mailing Address:", "Street Address:").
       - 'other': For any input that doesn't fit the above categories, such as phone numbers, email, or custom text (e.g., "Phone Number:", "Email Address:").
       Use only these types; do not invent new ones. Base your classification on the most logical fit from the surrounding text.

    3. **Provide a Description:** For each input, include a brief, concise, human-readable explanation of what the user is expected to provide. This should be 1-2 sentences at most, focusing on clarity without unnecessary details (e.g., "User must provide their full printed name in this field.").

    4. **Handle Variations and Edge Cases:** Documents may present input fields in diverse ways. Recognize variations such as:
       - Underscores or blank lines: Text like "Name: ____________________" indicates a 'full_name' input with marker_text "Name:".
       - Bracketed or parenthetical instructions: "Signature (required):" is a 'signature' with marker_text "Signature (required):".
       - Checkbox descriptions: "□ Agree to Terms" is a 'checkbox' with marker_text "Agree to Terms" (include the box symbol if present in text).
       - Multi-part fields: "Address: Street ________ City ________ State ____ Zip ____" should be treated as one 'address' input with marker_text "Address:".
       - Implicit fields: If text says "Please sign and date below" followed by blanks, identify separate 'signature' and 'date' inputs with appropriate markers like "Please sign and date below".

    5. **Examples of Analysis:** To guide your reasoning, consider these illustrative examples based on hypothetical document snippets:
       - Example 1: Text contains "Employee Name: ____________________". Output: A RequiredInput with input_type='full_name', marker_text='Employee Name:', description='User must print their full name here.'.
       - Example 2: Text contains "□ I accept the conditions". Output: RequiredInput with input_type='checkbox', marker_text='I accept the conditions', description='User must check this box to indicate acceptance.'.
       - Example 3: Text contains "Signature: ________ Date: ________". Output: Two RequiredInputs – one 'signature' with marker_text='Signature:', description='User must provide their signature.'; one 'date' with marker_text='Date:', description='User must enter the current date.'.
       - Example 4: Text contains "Initial each page: ____". Output: RequiredInput with input_type='initials', marker_text='Initial each page:', description='User must provide their initials on this page.'.
       - Example 5: Text contains purely instructional paragraphs with no blanks or labels for input. Output: An empty list for required_inputs.

    6. **Handle the "No Inputs" Case:** If the page consists solely of informational content, instructions, or static text without any fields, labels, or indicators for user input (e.g., no blanks, no "Sign here", no checkboxes), you MUST return an empty list for `required_inputs`. Do not fabricate inputs where none exist.

    7. **Strictly Adhere to the Schema:** Your final output MUST be a valid JSON object conforming exactly to the following Pydantic schema. Do not include any additional text, explanations, code, markdown, or characters outside this JSON object. The schema is:
       - PageInputAnalysis:
         - required_inputs: List[RequiredInput] (an array of objects; empty if no inputs)
       - RequiredInput:
         - input_type: str (one of the specified types)
         - marker_text: str (exact text from document)
         - description: str (brief explanation)

       Ensure the JSON is properly formatted, with double quotes around keys and strings, and no trailing commas.

    **Document Page Text to Analyze:**
    ---
    {page_text_content}
    ---

    **Final Reminder:** Output ONLY the JSON object. No introductions, conclusions, or extra content.
    """
    return prompt


def get_vllm_ocr_prompt() -> str:
    """
    Generates a prompt to instruct a Vision-Language Large Model (VLLM) to function as a highly accurate, formatting-aware Optical Character Recognition (OCR) engine for document image processing.
    """
    prompt = """
    **Your Role:** You are an advanced, state-of-the-art Vision-Language Large Model (VLLM) acting as a specialized Optical Character Recognition (OCR) engine. Your expertise lies in analyzing images of document pages, such as legal forms, contracts, reports, or administrative paperwork, and transcribing their textual content with exceptional precision. You are designed to recognize and preserve the structural and formatting elements of the document, ensuring the output is both accurate and usable for downstream processing.

    **Your Task:** Analyze the provided image of a single document page and transcribe its entire textual content into well-structured Markdown. Your transcription must reflect the exact content and layout of the document as it appears in the image, capturing all text and formatting elements such as headings, lists, and tables. This task is critical for automating document digitization, so your output must be reliable, consistent, and strictly adherent to the provided guidelines.

    **Critical Instructions:**

    1. **Preserve Document Structure and Formatting:**
       - **Headings:** Identify and format headings using appropriate Markdown syntax (e.g., `# Heading 1`, `## Heading 2`, etc.), based on font size, weight, or other visual cues indicating hierarchy.
       - **Lists:** Recognize ordered (numbered) and unordered (bulleted) lists, formatting them correctly in Markdown (e.g., `1. Item` for numbered lists, `- Item` for bulleted lists). Ensure indentation and nesting are preserved.
       - **Tables:** Detect tabular data and format it using Markdown table syntax (e.g., `| Column1 | Column2 |\n|---------|---------|\n| Data1   | Data2   |`). Align content accurately and include headers if present.
       - **Other Elements:** Preserve line breaks, paragraphs, and spacing as they appear. For example, a blank line in the document should be a blank line in the Markdown output.

    2. **Accuracy and Fidelity:**
       - Transcribe all visible text exactly as it appears in the image, preserving original wording, spelling, punctuation, and capitalization. Do not correct errors, paraphrase, or infer text that is not explicitly visible.
       - If text is partially legible or unclear (e.g., due to poor image quality), transcribe it to the best of your ability and do not insert placeholders or guesses unless explicitly instructed.
       - Handle special characters (e.g., ©, %, &, or currency symbols) accurately, using their correct representations in Markdown.

    3. **Clean and Focused Output:**
       - Your output must contain only the transcribed content in Markdown format. Do not include any commentary, explanations, analysis, or text that is not directly visible in the image.
       - Avoid adding metadata, assumptions, or interpretations about the document's purpose or context unless explicitly requested.
       - Ensure the Markdown is clean, syntactically correct, and free of unnecessary whitespace or formatting errors.

    4. **Handling Variations and Edge Cases:**
       - **Handwritten Text:** If the image contains handwritten notes, transcribe them as accurately as possible, treating them as regular text unless they are clearly part of a form field (e.g., a signature or filled-in blank).
       - **Form Fields:** For text near blanks, checkboxes, or lines (e.g., "Name: ____"), transcribe the label and represent the blank space with the exact characters used (e.g., underscores, or a blank space if none are present).
       - **Complex Layouts:** For multi-column layouts or mixed content (e.g., text with embedded images or logos), focus on transcribing the text in a logical reading order, using Markdown to approximate the structure as closely as possible.
       - **Examples of Expected Output:**
         - For a heading like "Section 1: Introduction" in bold, output: `# Section 1: Introduction`.
         - For a list like "• Item A\n• Item B", output: `- Item A\n- Item B`.
         - For a table like:
           ```
           Name    | Age
           --------|----
           John    | 30
           ```
           Output: `| Name | Age |\n|------|-----|\n| John | 30  |`.

    5. **Strict Schema Compliance:**
       - Your response must be a single, valid JSON object conforming to the following schema:
         - **VllmOcrResult**:
           - **markdown_content**: str (the complete transcribed text in clean Markdown format, including all headings, lists, tables, and other elements as they appear in the image).
       - Use double quotes for keys and string values, ensure proper JSON syntax, and avoid including any text, comments, or markdown outside the JSON object.
       - Example output: `{"markdown_content": "# Title\n\nParagraph text\n- Item 1\n- Item 2\n\n| Col1 | Col2 |\n|------|------|\n| Data | Data |"}`

    6. **Edge Case for Empty or Non-Text Images:**
       - If the image contains no text (e.g., a blank page or purely graphical content), return a JSON object with an empty string for `markdown_content`: `{"markdown_content": ""}`.
       - If the image is unreadable or corrupted, return an empty string for `markdown_content` and do not attempt to guess or fabricate content.

    **Final Reminder:**
    - Provide ONLY the JSON object containing the `markdown_content` field with the transcribed Markdown.
    - Do not include any additional text, explanations, code, or markdown outside the JSON object.
    - Ensure the output is precise, professional, and ready for automated processing.
    """
    return prompt


def get_multimodal_audit_prompt(
    nsv_markdown: str,
    sv_markdown: str,
    sv_ocr_text: str,
    required_inputs_analysis: dict,
    page_number: int  # <-- NEW ARGUMENT
) -> str:
    """
    Generates the master "5-Way" audit prompt for the VLLM.
    """
    
    prompt = f"""
    **Your Role:** You are a world-class Forensic Document Examiner with decades of experience in document authentication, fraud detection, and integrity verification. Your expertise encompasses analyzing digital and physical documents, including legal contracts, forms, applications, and official records, to identify discrepancies, fulfillments, and alterations. You approach each audit with meticulous attention to detail, cross-referencing multiple evidence sources to ensure impartial, accurate, and comprehensive findings. Your reports are used in high-stakes scenarios, so precision and professionalism are paramount.

    **Context:** You are auditing a single page from a multi-page document that exists in two versions: the Non-Signed Version (NSV), which is the original blank template, and the Signed Version (SV), which is the user-filled and potentially signed copy. The audit focuses on verifying that all required inputs have been properly fulfilled and that no unauthorized changes have been made to the static content. You are currently auditing **Page Number {page_number}** (1-indexed) of the document.

    **Evidence Package:** You will be provided with a multi-modal "evidence package" consisting of five interconnected sources:
    - **NSV Image:** (Visually inspect this via the provided image path) The original blank document page image, showing the template structure, labels, and blank fields.
    - **NSV Markdown:** A structured Markdown transcription of the NSV image, preserving headings, lists, tables, and text layout.
    - **SV Image:** (Visually inspect this via the provided image path) The filled/signed document page image, which may include user inputs like handwriting, checks, or stamps.
    - **SV Markdown:** A structured Markdown transcription of the SV image, capturing the filled content.
    - **SV OCR Text:** Raw text extracted from the SV image via OCR, useful for text comparison but potentially error-prone.
    Intelligently synthesize all five sources: Use images for visual confirmation (e.g., handwriting presence), Markdown for structured comparison, and OCR for textual diffs. Cross-verify inconsistencies across sources.

    **Your Two-Part Mission:**

    **Part 1: Audit Required Inputs**
    - Review the `Initial Analysis` (from NSV), which lists all required inputs identified on this page, including their type, marker_text, and description.
    - For each required input, meticulously examine the **SV Image** (primary source for visual elements like signatures or checks), **SV Markdown**, and **SV OCR Text** to determine if it has been fulfilled.
    - Fulfillment Criteria:
      - 'signature': Must show a visible signature (handwritten or electronic); blank or placeholder is not fulfilled.
      - 'date': Must contain a valid date format; empty or invalid is not fulfilled.
      - 'full_name': Must have a printed full name; partial or illegible is not fulfilled.
      - 'initials': Must show initials; missing is not fulfilled.
      - 'checkbox': Must indicate a check/mark (e.g., X or tick); unchecked is not fulfilled if required.
      - 'address': Must include complete address components; incomplete is not fulfilled.
      - 'other': Evaluate based on context (e.g., phone number must be present and valid).
    - Populate the `required_inputs` list with an entry for each, including `is_fulfilled` (bool) and `audit_notes` (detailed evidence-based explanation).

    **Part 2: Audit for Unauthorized Content Changes**
    - Compare the NSV evidence (NSV Markdown as baseline, cross-checked with NSV Image) against the SV evidence (SV Markdown, SV OCR Text, and SV Image).
    - Identify any changes to static, pre-written text (e.g., alterations to clauses, numbers, headings, or instructions).
    - **Ignore** changes that are authorized fillings of required inputs (e.g., a blank line now filled with a name).
    - **Report** any other discrepancies: additions, deletions, modifications, or reorderings that could alter meaning.
    - Use textual diff techniques: Align paragraphs, sentences, or words; note visual alterations in images (e.g., crossed-out text).
    - Populate the `content_differences` list with details if found; leave empty if none.

    **Determining Page Status:**
    - 'Verified': All required inputs fulfilled AND no content differences.
    - 'Input Missing': One or more required inputs not fulfilled (regardless of differences).
    - 'Content Mismatch': No missing inputs BUT unauthorized differences detected.
    - 'Input Missing and Content Mismatch': Both issues present (use this for combined errors).

    **Examples of Audit Findings:**
    - Example 1 (Input Audit): NSV has "Signature: ____". SV Image shows a scribble. Output: is_fulfilled=True, audit_notes='Handwritten signature visible in SV Image near marker.'.
    - Example 2 (Input Audit): NSV has "□ Agree". SV Markdown shows "□ Agree" unchanged. Output: is_fulfilled=False, audit_notes='Checkbox remains unchecked in SV evidence.'.
    - Example 3 (Content Diff): NSV: "Fee: $100". SV: "Fee: $50". Output: ContentDifference with nsv_text='Fee: $100', sv_text='Fee: $50', difference_type='modification', description='Amount reduced, potential fraud.'.
    - Example 4 (No Issues): All inputs filled, no diffs. Status: 'Verified', empty content_differences.
    - Example 5 (Edge Case): SV OCR has typos, but Image confirms no change. Ignore OCR error if Image/Markdown align with NSV.

    **Final Output Instructions:**
    - Your response MUST be a single, valid JSON object conforming to the schema below.
    - Do not include any text, explanations, or markdown outside the JSON.
    - Schema:
      - page_number: int (echo {page_number})
      - page_status: str (as defined above)
      - required_inputs: List[AuditedInput] (copy input_type, marker_text, description from initial; add is_fulfilled and audit_notes)
      - content_differences: List[ContentDifference] (empty if none)
    - Ensure JSON is properly formatted with double quotes, no trailing commas.

    ---
    **INITIAL ANALYSIS (from NSV):**
    {json.dumps(required_inputs_analysis, indent=2)}
    ---
    **NSV MARKDOWN:**
    {nsv_markdown}
    ---
    **SV MARKDOWN:**
    {sv_markdown}
    ---
    **SV OCR TEXT:**
    {sv_ocr_text}
    ---
    **Final Reminder:** Output ONLY the JSON object. No additional content.
    """
    return prompt