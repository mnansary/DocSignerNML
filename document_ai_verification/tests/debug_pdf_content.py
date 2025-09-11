import sys
from pathlib import Path

try:
    # Import the core MarkItDown class
    from markitdown import MarkItDown
except ImportError:
    print("Error: markitdown is not installed.")
    print("Please run: pip install 'markitdown[pdf]'")
    sys.exit(1)

def extract_markdown_from_pdf(pdf_path: Path):
    """
    Opens a PDF file using the markitdown library, extracts the content
    as Markdown, and prints the result to the console.
    """
    # --- 1. Validate Input File ---
    if not pdf_path.is_file():
        print(f"❌ Error: File not found at the specified path.")
        print(f"   Attempted path: {pdf_path.resolve()}")
        return

    print(f"📄 Analyzing PDF with MarkItDown: {pdf_path.name}")
    print("=" * 70)

    try:
        # --- 2. Initialize MarkItDown ---
        # We don't need any plugins for this basic conversion
        md_converter = MarkItDown()

        # --- 3. Perform the Conversion ---
        # The convert method handles reading the file and extracting content
        result = md_converter.convert(str(pdf_path))

        # --- 4. Print the Result ---
        if result and result.text_content:
            print("✅ Conversion Successful! Extracted Markdown Content:")
            print("-" * 70)
            print(result.text_content)
            print("-" * 70)
            print(f"Total Character Count: {len(result.text_content)}")
        else:
            print("⚠️ Warning: MarkItDown did not return any text content for this file.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during MarkItDown conversion: {e}")
        print("   Please ensure the PDF is not corrupted and that all dependencies are installed correctly.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_markdown_extractor.py <path_to_your_pdf_file>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    extract_markdown_from_pdf(file_path)