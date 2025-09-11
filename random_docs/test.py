import json
from pathlib import Path
from PIL import Image, ImageDraw

def draw_bounding_boxes(image_path: Path, json_data_str: str, output_path: Path, color: str = "red", line_width: int = 3):
    """
    Opens an image, draws bounding boxes on it based on JSON data, and saves the result.

    Args:
        image_path (Path): Path to the input image file.
        json_data_str (str): A string containing the JSON data with detections.
        output_path (Path): Path to save the new image with boxes drawn on it.
        color (str): The color of the bounding box lines.
        line_width (int): The width of the bounding box lines in pixels.
    """
    # --- 1. Load the Image ---
    try:
        image = Image.open(image_path).convert("RGB") # Convert to RGB to ensure color drawing works
    except FileNotFoundError:
        print(f"❌ Error: Input image not found at '{image_path}'")
        return

    # --- 2. Parse the JSON Data ---
    try:
        data = json.loads(json_data_str)
        detections = data.get("detections", [])
        if not detections:
            print("⚠️ Warning: JSON data does not contain any 'detections'.")
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON string provided.")
        return

    # --- 3. Draw the Bounding Boxes ---
    draw = ImageDraw.Draw(image)
    
    print(f"Found {len(detections)} detection(s) to draw.")
    for i, detection in enumerate(detections):
        box = detection.get("box")
        if box and len(box) == 4:
            # The rectangle method takes a list or tuple of [x1, y1, x2, y2]
            draw.rectangle(box, outline=color, width=line_width)
            print(f"  -> Drew box {i+1}: {box}")
        else:
            print(f"  -> Skipped invalid box data in detection {i+1}: {detection}")

    # --- 4. Save the New Image ---
    try:
        image.save(output_path)
        print(f"\n✅ Successfully saved image with bounding boxes to '{output_path}'")
    except Exception as e:
        print(f"❌ Error: Could not save the output image. Reason: {e}")


if __name__ == "__main__":
    # --- Configuration ---
    # Assume this script is in the project root, alongside the sample image.
    project_root = Path(__file__).parent
    
    # Input image file (must exist)
    input_image_file = project_root / "sample_document.png"
    
    # Output file (will be created)
    output_image_file = project_root / "sample_document_with_boxes.png"

    # The JSON output from your VLLM test
    vllm_json_output = """
    {
      "detections": [
        {
          "box": [
            683,
            820,
            833,
            920
          ]
        },
        {
          "box": [
            870,
            820,
            980,
            920
          ]
        }
      ]
    }
    """
    
    print("--- Starting Bounding Box Drawing Test ---")
    
    # Run the drawing function
    draw_bounding_boxes(
        image_path=input_image_file,
        json_data_str=vllm_json_output,
        output_path=output_image_file
    )