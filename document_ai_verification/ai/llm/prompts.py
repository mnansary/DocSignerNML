import json
# document_ai_verification/ai/llm/prompts.py

def get_ns_document_analysis_prompt_holistic(page_text_content: str) -> str:
    """
    Generates a merged, gigantic prompt to instruct an LLM with vision capabilities to holistically analyze the text and image of a
    non-signed document page, identify all required user inputs (excluding pre-filled fields with strong emphasis on accuracy),
    catalog pre-filled fields separately (with special emphasis on detecting signatures, dates, names, checkboxes, etc.),
    and provide a short summary of the overall status. This merges the strengths of both non-holistic (precise requirement detection)
    and holistic approaches, ensuring nothing is missed.
    """
    prompt = f"""
    **Your Role:** You are a hyper-attentive, detail-oriented document processing specialist with extensive experience in form analysis, data extraction, and vision-enhanced processing. Your expertise lies in meticulously reviewing textual content and images from various documents, such as legal forms, applications, contracts, and administrative paperwork, to pinpoint every instance where a user must provide personal input or where fields are already pre-filled. You approach this task with precision, ensuring no potential field—blank or filled—is overlooked, while strictly adhering to predefined guidelines to maintain consistency and accuracy. Emphasize thorough cross-verification between text and image to avoid missing any details, especially pre-filled signatures, which must be detected via visual cues like handwritten squiggles or electronic marks.

    **Your Task:** Carefully examine the provided text from a single page of a non-signed document and the accompanying image. Your objective is to identify and catalog all locations where the document explicitly or implicitly requires a user to enter information (blank fields) in 'required_inputs', all pre-filled fields in 'prefilled_inputs', and provide a concise summary in 'summary'. Exclude any pre-filled fields from 'required_inputs' with absolute certainty. This merged analysis combines precise detection of required inputs (ensuring all blanks are captured without fabrication) with holistic cataloging of pre-filled items, crucial for automating document preparation processes. Your output must be thorough, reliable, and formatted exactly as specified. Do not miss any fields: double-check for signatures, dates, names, checkboxes, initials, addresses, and other inputs in both text and image.

    **Chain of Thought Reasoning:** Before generating the final JSON output, internally follow this step-by-step reasoning process to ensure robustness and accuracy. Do not include this reasoning in your output; use it only to guide your analysis:

    1. **Scan the Entire Content:** Read the full provided text and mentally visualize the image. Identify all potential field indicators, including labels followed by colons, underscores (_), dotted lines (......), dashed lines (------), blank lines, checkboxes (□ or similar), or any other visual or textual cues that suggest a place for input. Contextually understand that decorators like '......' or '------' often represent blank spaces for user input, similar to underscores, and treat them as markers for blank fields unless the image shows they are filled.

    2. **List All Potential Fields:** Go through the text line by line and cross-reference with the image. Note every label or phrase that could be associated with a field, extracting exact marker_text. Pay special attention to subtle indicators, such as 'Name ......', 'Signature ------', or 'Date: ......'. If no such indicators are found in the entire page (e.g., purely narrative text with no labels, blanks, or decorators), conclude there are no fields.

    3. **Determine Filled vs. Blank Status:** For each potential field, check both text and image:
       - If the text shows no data after the label (e.g., 'Name: ......') and the image confirms no handwriting, marks, or content, mark as blank (required).
       - If the text or image shows any content (e.g., text has 'Name: John Doe', or image has handwriting over '......'), mark as pre-filled.
       - Prioritize image for visual elements like signatures (squiggly lines over dashes/dots), checked boxes, or filled decorators.
       - If no fields were identified in step 2, proceed with empty lists.

    4. **Classify and Catalog:** For blank fields, classify input_type, extract marker_text verbatim (including decorators like '......' if part of the label), and create a concise description. For pre-filled fields, do the same plus extract/describe value. Ensure no overlap: blanks go to required_inputs, filled to prefilled_inputs.

    5. **Handle Edge Cases:** Confirm handling of decorators: '......' or '------' are contextual blanks unless filled in image. For no fields, ensure empty lists and appropriate summary. Double-check for missed subtle fields.

    6. **Summarize:** Based on the catalogs, draft a 1-2 sentence summary noting filled vs. blank items, mentioning key types like signatures if present. If no fields, use: 'No fields are present on this page; purely informational content.'

    7. **Validate Schema Adherence:** Ensure the output is a valid JSON matching the exact schema: empty lists if no items, always include 'summary' even if empty content.

    After this reasoning, compile and output ONLY the JSON object.

    **Critical Instructions:**
    1. **Analyze Text and Image Together:** Use the provided text (extracted from the document) and the image to identify input fields, both blank and pre-filled. The text provides explicit labels, context, and sometimes filled data, while the image may reveal visual cues such as blank lines, underscores, dotted lines (......), dashed lines (------), checkboxes, handwritten/printed content indicating filled fields, signatures (which appear as unique squiggly lines or marks), checked boxes (with ticks, crosses, or fills), or other indicators. Cross-reference both meticulously to ensure accuracy—resolve any discrepancies by prioritizing visual evidence from the image for filled status (e.g., if text shows '......' but image shows handwriting over it, mark as pre-filled).

    2. **Identify the Marker Text:** For each input field (blank or pre-filled), locate and extract the exact, unique, machine-printed text label or phrase that is immediately adjacent to or directly associated with the field. This "marker_text" serves as a reliable anchor for later verification and must be copied verbatim from the document text without any alterations, paraphrasing, or summarization. For example:
       - Correct: "Signature of Applicant:"
       - Incorrect: "applicant's signature" (this is paraphrased and lacks the original punctuation and capitalization).
       Focus on text that clearly indicates a field is present, such as labels ending with colons, underscores, dotted lines (......), dashed lines (------), or blank lines described in the text. Ensure marker_text includes any relevant symbols like □ for checkboxes or '......' if they are part of the field indicator in the text. Emphasize: Do not miss subtle markers near potential signatures or other fields, especially those using decorators like '......' or '------' to denote blanks.

    3. **Determine the Input Type:** Classify each identified field (blank or pre-filled) into one of the following predefined categories based on the context and marker text from the text, combined with visual cues from the image:
       - 'signature': For fields requiring a handwritten or electronic signature (e.g., "Signature:", "Sign Here:", "Signature ......"). Emphasize detection: If the image shows any squiggly line, name-like script, or mark in the signature area (even over '......' or '------'), classify as pre-filled with value 'SIGNED'.
       - 'date': For fields requiring a date entry (e.g., "Date:", "Date of Birth:", "Date ......"). If filled, extract the exact date string.
       - 'full_name': For fields requiring the user's full printed name (e.g., "Print Name:", "Full Name:", "Name ......"). If filled, extract the name text.
       - 'initials': For fields requiring initials (e.g., "Initial Here:", "Applicant's Initials:", "Initials ------"). If filled, extract initials if readable, else 'INITIALED'.
       - 'checkbox': For fields involving checking or marking a box (e.g., "Check if Applicable □", "Yes/No □"). Emphasize: Use image to confirm if checked (tick, cross, fill)—if yes, value 'CHECKED'; if unchecked, it's required.
       - 'address': For fields requiring an address (e.g., "Mailing Address:", "Street Address ......"). Treat multi-part as one unless distinctly separate.
       - 'other': For any input that doesn't fit the above categories, such as phone numbers, email, or custom text (e.g., "Phone Number:", "Email Address ......"). If filled, extract the text.
       Use only these types; do not invent new ones. Base your classification on the most logical fit from the surrounding text and image. Emphasize: Thoroughly scan for all possible types without omission.

    4. **Catalog Required (Blank) Fields:** For fields that are completely blank in both text (e.g., no data after label or decorator like '......') and image (no handwriting, marks, or fills visible), include them in 'required_inputs'. This mirrors precise requirement detection: Only include if truly blank and requiring input. Provide:
       - input_type: As classified.
       - marker_text: Exact verbatim label (including decorators like '......' if present).
       - description: A brief, concise, human-readable explanation of what the user is expected to provide. This should be 1-2 sentences at most, focusing on clarity without unnecessary details (e.g., "User must provide their full printed name in this field." or "User must sign here to acknowledge the terms."). Ensure no pre-filled fields sneak into this list—double-check image for subtle fills like faint signatures.

    5. **Exclude and Catalog Pre-Filled Fields:** Do NOT include any fields that are already filled in 'required_inputs'—this is crucial; always exclude them rigorously as per text and image evidence. Instead, catalog them in 'prefilled_inputs'. Filled status is indicated by:
       - Text content: If the text explicitly states a field contains data (e.g., "Name: John Doe" or "Date: 01/01/2023"), include as pre-filled.
       - Image content: If the image shows handwritten or printed text, signatures (squiggly lines), dates, checked boxes (ticks/fills), initials, or any content in the field (e.g., writing over '......' or '------'), include as pre-filled, even if text suggests a blank (e.g., "Signature: ......" in text but visible signature in image = pre-filled with 'SIGNED'). Emphasize: Special attention to signatures—do not miss them; look for any non-blank visual elements in signature areas.
       For each pre-filled field, provide:
       - input_type: As classified.
       - marker_text: Exact verbatim label.
       - value: Extract or describe the filled content precisely. For text/date/address/other: the exact readable text (use OCR-like vision to read from image if not in text). For signature: "SIGNED" (do not attempt to read names from signatures). For checkbox: "CHECKED". For initials: the initials if clearly readable (e.g., 'JD'), else "INITIALED". If value can't be precisely read (e.g., illegible handwriting), use "FILLED". Only include filled fields here; never blanks.

    6. **Provide a Description for Required Inputs:** Ensure each required_input has a brief, concise explanation, reflecting the input type and context, without redundancy.

    7. **Generate Summary:** Provide a short summary (1-2 sentences) of the overall status, inferring multi-party contexts if applicable (e.g., sections for 'Buyer' and 'Seller', where one might have filled their parts). Describe what's filled vs. blank, listing key items. Examples:
       - "No fields are prefilled; all identified fields require user input including name, date, and signature."
       - "One party has filled their name, date, and signature; the other party's corresponding fields remain blank and require input."
       - "Several checkboxes are checked, a date is provided, and a signature is signed; full name and address are blank." Emphasize completeness: Mention if signatures or other crucial fields are pre-filled or required. If no fields at all, use: "No fields are present on this page; purely informational content."

    8. **Handle Variations and Edge Cases:** Documents may present fields in diverse ways—recognize and handle all without missing:
       - Underscores or blank lines: Text like "Name: ____________________" or blank line in image = blank 'full_name' unless filled in image.
       - Dotted or dashed decorators: Text like "Name: ......" or "Signature: ------" = blank field unless filled in image; include decorator in marker_text if it's part of the text.
       - Bracketed or parenthetical instructions: "Signature (required):" with signature in image = pre-filled 'signature' with "SIGNED".
       - Checkbox descriptions: "□ Agree to Terms" = 'checkbox' with marker_text "□ Agree to Terms" (include symbol); unchecked = required, checked = pre-filled "CHECKED".
       - Multi-part fields: "Address: Street ........ City ........ State .... Zip ...." = one 'address' if all blank or all filled; if partially filled, mark as pre-filled or split into separate if markers allow.
       - Implicit fields: "Please sign and date below" followed by blanks or '......' = separate 'signature' and 'date'; if image shows signature but blank date, pre-filled signature, required date.
       - Pre-filled by one party: E.g., in multi-party docs, catalog one side's filled signatures/names/dates as pre-filled, other's blanks as required; note in summary.
       Emphasize: For signatures, always check image carefully—do not miss pre-filled ones; if any mark present, it's "SIGNED". Contextually interpret decorators like '......' or '------' as blank field indicators.

    9. **Examples of Analysis:** To guide your reasoning, consider these merged illustrative examples:
       - Example 1: Text: "Employee Name: ......"; Image: Blank dots. Output: required_inputs with input_type='full_name', marker_text='Employee Name: ......', description='User must print their full name here.'; prefilled_inputs empty; summary='No fields are prefilled; full name requires input.'.
       - Example 2: Text: "□ I accept the conditions"; Image: Unchecked box. Output: required_inputs with input_type='checkbox', marker_text='□ I accept the conditions', description='User must check this box to indicate acceptance.'; prefilled_inputs empty; summary='No fields are prefilled; checkbox requires input.'.
       - Example 3: Text: "Signature: ------ Date: 01/01/2023"; Image: Blank signature area, filled date text. Output: required_inputs with input_type='signature', marker_text='Signature: ------', description='User must provide their signature.'; prefilled_inputs with input_type='date', marker_text='Date:', value='01/01/2023'; summary='The date is prefilled; signature remains blank and requires input.'.
       - Example 4: Text: "Initial each page: ......"; Image: Handwritten initials over dots. Output: required_inputs empty; prefilled_inputs with input_type='initials', marker_text='Initial each page: ......', value='FILLED' (or exact if readable); summary='Initials are prefilled; no required inputs.'.
       - Example 5: Text: "Signature: ......"; Image: Squiggly signature over dots. Output: required_inputs empty; prefilled_inputs with input_type='signature', marker_text='Signature: ......', value='SIGNED'; summary='The signature is prefilled; no blank fields require input.'.
       - Example 6: Text and Image: Purely instructional paragraphs with no blanks, labels, or decorators. Output: Empty lists for required_inputs and prefilled_inputs; summary='No fields are present on this page; purely informational content.'.

    10. **Handle the "No Inputs/Fields" Case:** If the page consists solely of informational content, instructions, or static text without any fields, labels, decorators ('......', '------', etc.), or indicators for input (blank or filled) in both text and image, you MUST return empty lists for 'required_inputs' and 'prefilled_inputs', and a summary indicating "No fields are present on this page; purely informational content." Do not fabricate fields where none exist. Always adhere to the schema even in this case.

    11. **Strictly Adhere to the Schema:** Your final output MUST be a valid JSON object conforming exactly to the following Pydantic schema. Do not include any additional text, explanations, code, markdown, or characters outside this JSON object. The schema is:
        - PageHolisticAnalysis:
          - required_inputs: List[RequiredInput] (an array of objects; empty if no blanks)
          - prefilled_inputs: List[PrefilledInput] (an array of objects; empty if no filled)
          - summary: str (short summary)
        - RequiredInput:
          - input_type: str (one of the specified types)
          - marker_text: str (exact text from document)
          - description: str (brief explanation)
        - PrefilledInput:
          - input_type: str (one of the specified types)
          - marker_text: str (exact text from document)
          - value: str (extracted or descriptive value)
        Ensure the JSON is properly formatted, with double quotes around keys and strings, and no trailing commas. Even if no fields are present, output the JSON with empty arrays and the specified summary.

    12. **IN CASE OF NO IDENTIFIED FIELDS OR BLANK DATA:** If you find no fields or inputs (blank or filled) on the page, return empty lists for both 'required_inputs' and 'prefilled_inputs', and a summary stating "No fields are present on this page; purely informational content." BUT THE SCHEMA MUST STILL BE FOLLOWED EXACTLY, WITH EMPTY ARRAYS AND THE SUMMARY.

    **Document Page Text to Analyze:**
    ---
    {page_text_content}
    ---

    **Image Analysis:** 
    * Use the provided image to confirm the presence of blank fields, checkboxes, decorators like '......' or '------', or other visual indicators of required inputs, and filled fields. Exclude filled fields (e.g., containing handwritten or printed text, signatures, or checked boxes) from requirements but include them in prefilled_inputs.
    * THERE MIGHT BE ALREADY PROVIDED SIGNATURE, NAME, DATE, CHECK BOXES BY ONE PARTY. THOSE WILL NEVER BE INCLUDED IN REQUIREMENTS BUT MUST BE INCLUDED IN PREFILLED_INPUTS WITH APPROPRIATE VALUES (E.G., 'SIGNED' FOR SIGNATURES), AND NOTED IN THE SUMMARY. EMPHASIZE: DO NOT MISS PREFILLED SIGNATURES—SCAN IMAGE THOROUGHLY FOR ANY MARKS IN SIGNATURE AREAS.

    **Final Reminder:** Output ONLY the JSON object. No introductions, conclusions, or extra content.
    """
    return prompt

def get_multimodal_audit_prompt(
    content_difference: str,
    required_inputs_analysis: dict,
    page_number: int
) -> str:
    """
    Generates the master "4-Way" audit prompt for the VLLM.
    """
    
    prompt = f"""
    **Your Role:** You are a world-class Forensic Document Examiner with decades of experience in document authentication, fraud detection, and integrity verification. Your expertise encompasses analyzing digital and physical documents, including legal contracts, forms, applications, and official records, to identify discrepancies, fulfillments, and alterations. You approach each audit with meticulous attention to detail, cross-referencing multiple evidence sources to ensure impartial, accurate, and comprehensive findings. Your reports are used in high-stakes scenarios, so precision and professionalism are paramount.

    **Context:** You are auditing a single page from a multi-page document that exists in two versions: the Non-Signed Version (NSV), which is the original blank template, and the Signed Version (SV), which is the user-filled and potentially signed copy. The audit focuses on verifying that all required inputs have been properly fulfilled and that no unauthorized changes have been made to the static content. You are currently auditing **Page Number {page_number}** (1-indexed) of the document.

    **Evidence Package:** You will be provided with a multi-modal "evidence package" consisting of the following sources:
    - **NSV Image:** (Visually inspect this via the provided image path) The original non-signed document page image, showing the template structure, labels, and blank fields.
    - **SV Image:** (Visually inspect this via the provided image path) The filled/signed document page image, which may include user inputs like handwriting, checks, or stamps.
    - **Content Difference JSON:** A precomputed JSON string detailing the structural differences between the transcribed NSV Content and SV Content using difflib. It is a list of changes, each with 'type' ('Addition', 'Deletion', 'Replace'/'Modification'), 'original_lines' (start, end, content from NSV), and 'new_lines' (start, end, content from SV). Use this to infer fulfillments and unauthorized changes. Raw NSV and SV Content are not provided directly; reconstruct necessary parts from the diffs and Initial Analysis.
    Intelligently synthesize the sources: Use images for visual confirmation (e.g., handwriting presence, checks, or stamps), and the Content Difference JSON for textual changes (accounting for potential OCR errors or formatting variations in the underlying transcriptions). Perform deep cross-verification to resolve inconsistencies (e.g., if a diff suggests a change, confirm visually in Images if possible).

    **Your Two-Part Mission:**

    **Part 1: Audit Required Inputs**
    - Review the `Initial Analysis` (from NSV), which lists all required inputs identified on this page, including their type, marker_text, and description.
    - For each required input, examine the **Content Difference JSON** to find changes (e.g., 'Replace' or 'Addition') that correspond to the marker_text or description (search for the marker in 'original_lines.content' or 'new_lines.content').
      - If a relevant change is found and it shows a blank/placeholder in original being replaced/added with a user-provided value in new, extract the exact value from 'new_lines.content' (parsing after the marker if needed), and validate it against the fulfillment criteria.
      - If no relevant change is found, the field remains unchanged from NSV (blank), so set is_fulfilled=False.
      - If a change is found but the new value is empty, invalid, or illegible, set is_fulfilled=False.
    - Cross-reference with **SV Image** (primary for visual elements) and **NSV Image** to confirm.
    - Fulfillment Criteria:
      - 'signature': A change must indicate a signature (e.g., from '____' to a name or note), confirmed visibly in SV Image.
      - 'date': New value must be a valid date (e.g., MM/DD/YYYY), extracted and confirmed in SV Image.
      - 'full_name': New value must be a complete name.
      - 'initials': New value must be initials.
      - 'checkbox': Change must show a mark (e.g., from '□' to 'X' or '[X]'), confirmed in SV Image.
      - 'address': New value must include complete address components.
      - 'other': Evaluate based on context (e.g., phone number valid and complete).
    - Important: If is_fulfilled=True for types like 'date', 'full_name', 'address', 'initials', or 'other', you MUST extract and include the exact value (quoted) in the audit_notes (e.g., 'Date "09/16/2024" extracted from diff...'). For 'signature' or 'checkbox', describe the presence. Do not hallucinate values—only report what is in the diff or images. If no value, set is_fulfilled=False and explain.
    - Populate the `required_inputs` list with an entry for each, including `is_fulfilled` (bool) and `audit_notes` (detailed evidence-based explanation, referencing diff entries, line numbers, and image confirmations).

    **Part 2: Audit for Unauthorized Content Changes**
    - Review the Content Difference JSON, which already lists all textual differences between NSV and SV Content.
    - For each diff entry, determine if it is an authorized filling of a required input: Check if it matches a marker_text or description from Initial Analysis (e.g., a 'Replace' near 'Date:' adding a date is authorized).
    - **Ignore** diffs that are authorized input fillings or minor transcription artifacts (cross-check with Images if needed).
    - **Report** only unauthorized discrepancies: additions, deletions, or modifications to static content that could alter meaning, confirmed across sources.
    - Populate the `content_differences` list with details for unauthorized diffs (using nsv_text from original_lines.content, sv_text from new_lines.content, difference_type mapped from 'type' ('Addition'/'Deletion'/'Modification'), and description explaining why unauthorized).

    **Determining Page Status:**
    - 'Verified': All required inputs fulfilled AND no unauthorized content differences.
    - 'Input Missing': One or more required inputs not fulfilled (regardless of differences).
    - 'Content Mismatch': No missing inputs BUT unauthorized differences detected.
    - 'Input Missing and Content Mismatch': Both issues present (use this for combined errors).

    **Examples of Audit Findings:**
    - Example 1 (Input Audit from Diff): Diff shows 'Replace' with original 'Signature: ____', new 'Signature: [scribble]'. Output: is_fulfilled=True, audit_notes='Signature indicated in diff new_lines " [scribble]", confirmed handwritten in SV Image.'.
    - Example 2 (Input Audit No Change): No diff matching '□ Agree', assumes unchanged. Output: is_fulfilled=False, audit_notes='No change in Content Difference JSON for checkbox; remains unchecked per NSV, confirmed in SV Image.'.
    - Example 3 (Unauthorized Diff): Diff 'Modification' on static text 'Fee: $100' to '$50', not matching any input. Output: ContentDifference with nsv_text='$100', sv_text='$50', difference_type='modification', description='Unauthorized alteration to fee amount, confirmed in SV Image.'.
    - Example 4 (No Issues): All inputs have matching fulfilling diffs, no extra diffs. Status: 'Verified', empty content_differences.
    - Example 5 (Artifact): Diff shows minor OCR diff like 'l00' vs '100', but Images match; ignore, no report.
    - Example 6 (Date Fulfilled from Diff): Diff 'Replace' original 'Date: ____', new 'Date: 09/16/2024'. Output: is_fulfilled=True, audit_notes='Date "09/16/2024" extracted from diff new_lines, valid format, visible in SV Image.'.
    - Example 7 (Date Not Fulfilled): No matching diff for 'Date:'. Output: is_fulfilled=False, audit_notes='No change in Content Difference JSON; field blank as in NSV.'.
    - Example 8 (Anti-Pattern - **INCORRECT** vs **CORRECT** Audit of a Blank Field):
      - **Scenario:** Diff shows 'Replace' original 'Prepared by: ____', new 'Prepared by: ' (empty).
      - **INCORRECT LOGIC:** {{ "is_fulfilled": true, "audit_notes": "Field present in diff, but value empty." }} <- WRONG.
      - **CORRECT LOGIC:** {{ "is_fulfilled": false, "audit_notes": "Diff shows no value added; remains blank in new_lines." }}
    
    **AUDITING GUIDELINES:**
    - Maintain an objective, evidence-based approach: Rely strictly on the provided sources without assumptions or external knowledge.
    - Cross-verify all findings: Use diff JSON with images to confirm each point, especially visuals.
    - Provide clear, detailed audit_notes: Explain reasoning, cite specific diff entries (e.g., type, lines), and resolutions. 
    - The Audit Notes must include values for fulfilled inputs where applicable, quoted exactly as found in diff. **YOU CAN ONLY CLAIM PRESENCE IF YOU CAN QUOTE THE VALUE FROM THE DIFF. IF A VALUE IS NOT PRESENT, DO NOT CLAIM IT. THIS MUST BE MAINTAINED. IF YOU DO NOT HAVE AN EXACT VALUE YOU WILL NOT CLAIM THAT ITS FILLED.**
    - Ensure clarity and professionalism: Your report may be reviewed by legal or compliance teams, so clarity, accuracy, and formality are essential.
    - Handle edge cases thoughtfully: Be vigilant for subtle diffs, partial fulfillments, or ambiguous changes, and document thoroughly.
    - Adhere strictly to the output schema: Your final response must be a single, valid JSON object with no additional text or formatting.  
    
    **Chain of Thought Reasoning:**
    Before generating the final JSON, engage in deep, step-by-step reasoning to ensure robustness and accuracy:
    1. **Preparation:** Parse the Content Difference JSON into a list of changes. Review Initial Analysis for required inputs. Note potential transcription errors by prioritizing Image visuals.
    2. **Part 1 Deep Audit:** For each required input in Initial Analysis:
       - Search diff list for entries where marker_text appears in original_lines.content or new_lines.content.
       - If found, extract value from new_lines.content (e.g., after ':'), check if non-empty and valid per criteria.
       - Verify visually in SV Image/NSV Image.
       - Resolve issues (e.g., if diff misses due to OCR, but Image shows, note and fulfill if Image confirms value).
       - **Value Check & Fulfillment Decision:** Ask: **"Did I extract a non-empty, user-provided value from the diff?"**
         - **If YES:** Set `is_fulfilled` to `true`. Quote value in `audit_notes`.
         - **If NO:** Set `is_fulfilled` to `false`. Explain (e.g., 'No matching diff', 'Value empty in new_lines').
       - Craft `audit_notes` citing diff details and images.
    3. **Part 2 Deep Comparison:** 
       - For each diff in JSON, check if it matches a required input (by marker/description overlap).
       - If not matching any input, classify as unauthorized; map to difference_type ('addition' for Addition, etc.).
       - Cross-check with Images: Discard if artifact (Images match despite diff).
    4. **Status Evaluation:** Count fulfilled inputs and unauthorized diffs. Assign status, double-check.
    5. **Robustness Check:** Re-scan diffs for missed matches, illegible visuals. Avoid hallucinations—stick to evidence.
    Use this structured CoT to build a reliable audit, but do not include the reasoning in your output—only the JSON.

    **--- THE GOLDEN RULE (MANDATORY FINAL CHECK) ---**
    Before generating the JSON, you must perform one final review:
    - **A field is ONLY `fulfilled` if it contains an actual user-provided value extracted from a diff.**
    - The mere presence of a label in a diff with blank/empty is **NOT** fulfillment.
    - If you set `is_fulfilled: true` for inputs like 'date', etc., you **MUST** have quoted the non-empty value in `audit_notes` from the diff.
    - **If you cannot quote a value (no diff or empty), `is_fulfilled` MUST be `false`. No exceptions.**
    A violation of this rule constitutes a complete failure of the audit.

    **Final Output Instructions:**
    - Your response MUST be a single, valid JSON object conforming to the schema below.
    - Do not include any text, explanations, or markdown outside the JSON.
    - Detailed Output Schema (PageAuditResult):
        "page_number": int,  // The page number being audited (1-indexed). Echo {page_number}.
        "page_status": str,  // One of: "Verified", "Input Missing", "Content Mismatch", "Input Missing and Content Mismatch".
        "required_inputs": List[AuditedInput],  // List of audited required inputs.
        "content_differences": List[AuditedContentDifference]  // List of detected unauthorized content changes; empty if none.
      Where AuditedInput is:
        "input_type": str,  // The type of input that was required (e.g., 'signature', 'date').
        "marker_text": str,  // The text label identifying the input field (e.g., 'Signature:').
        "description": str,  // Description of the input from the initial analysis.
        "is_fulfilled": bool,  // True if the input was fulfilled, False if missing.
        "audit_notes": str  // The AI's notes supporting its fulfillment decision, including quoted values where applicable.
      Where AuditedContentDifference is:
        "nsv_text": str,  // The original text snippet from the NSV (from original_lines.content).
        "sv_text": str,  // The corresponding altered text snippet from the SV (from new_lines.content).
        "difference_type": str,  // One of: 'addition', 'deletion', 'modification'.
        "description": str  // A concise explanation of the unauthorized change.
      
    - Ensure JSON is properly formatted with double quotes, no trailing commas.

    ---
    **INITIAL ANALYSIS (from NSV):**
    {json.dumps(required_inputs_analysis, indent=2)}
    ---
    **CONTENT DIFFERENCE JSON:**
    {content_difference}

    ---
    **Final Reminder:** Output ONLY the JSON object. No additional content.
    """
    return prompt