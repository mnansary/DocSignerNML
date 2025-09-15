import difflib
import json

def get_structured_diff_json(text1: str, text2: str) -> str:
    """
    Compares two strings and returns a JSON string detailing the differences.

    The function identifies additions, deletions, replacements, and equal parts,
    providing line numbers and the text content for each segment.

    Args:
        text1: The first string (original text).
        text2: The second string (new text).

    Returns:
        A JSON formatted string representing the list of differences.
    """
    # Split texts into lines for comparison
    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()

    # Create a SequenceMatcher instance
    matcher = difflib.SequenceMatcher(None, text1_lines, text2_lines)

    diff_list = []

    # get_opcodes() returns a list of 5-tuples describing the differences
    # (tag, i1, i2, j1, j2)
    # tag: 'replace', 'delete', 'insert', 'equal'
    # i1:i2: slice indices for text1
    # j1:j2: slice indices for text2
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        # We don't need to include the 'equal' parts in the JSON
        # but you could if you wanted a complete representation of the file
        if tag == 'equal':
            continue

        change_type = tag.capitalize() # 'replace' -> 'Replace'
        if tag == 'insert':
            change_type = 'Addition'
        elif tag == 'delete':
            change_type = 'Deletion'
        
        diff_list.append({
            "type": change_type,
            "original_lines": {
                "start": i1 + 1,
                "end": i2,
                "content": "\n".join(text1_lines[i1:i2])
            },
            "new_lines": {
                "start": j1 + 1,
                "end": j2,
                "content": "\n".join(text2_lines[j1:j2])
            }
        })

    # Convert the list of dictionaries to a JSON string
    return json.dumps(diff_list, indent=4)
