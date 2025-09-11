import os
import json
import logging
import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, BadRequestError
from typing import Generator, Any, Type, TypeVar, List
from pydantic import BaseModel, Field

def build_structured_prompt(prompt: str, response_model: Type[BaseModel]) -> str:
    """
    Constructs a standardized prompt for forcing a model to generate a
    JSON object that conforms to a given Pydantic model's schema.
    
    Args:
        prompt (str): The core user prompt or request.
        response_model (Type[BaseModel]): The Pydantic model for the desired output.

    Returns:
        str: A fully formatted prompt ready for an LLM.
    """
    # Generate the JSON schema from the Pydantic model.
    schema = json.dumps(response_model.model_json_schema(), indent=2)

    # Engineer a new prompt that includes the original prompt and instructions.
    structured_prompt = f"""
    Given the following request:
    ---
    {prompt}
    ---
    Your task is to provide a response as a single, valid JSON object that strictly adheres to the following JSON Schema.
    Do not include any extra text, explanations, or markdown formatting (like ```json) outside of the JSON object itself.

    JSON Schema:
    {schema}
    """
    return structured_prompt


# Load environment variables from a .env file
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Generic type variable for Pydantic models for clean type hinting.
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

class ContextLengthExceededError(Exception):
    """Custom exception for when a prompt exceeds the model's context window."""
    pass

def encode_image_to_base64(image_path: Path) -> str:
    """Reads an image file and returns its base64 encoded string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"Error encoding image {image_path}: {e}")
        raise

class LLMService:
    """
    A synchronous client for OpenAI-compatible APIs using the 'openai' library.
    """
    def __init__(self,api_key:str ,model: str, base_url: str, max_context_tokens: int):
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
        print(f"✅ LLMService (Sync) initialized for model '{self.model}' with max_tokens={self.max_context_tokens}.")

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
            return response.choices[0].message.content or ""
        except BadRequestError as e:
            if "context length" in str(e).lower() or "too large" in str(e).lower():
                logging.error(f"Prompt exceeded context window for model {self.model}.")
                raise ContextLengthExceededError(f"Prompt is too long for the model's {self.max_context_tokens} token limit.") from e
            else:
                logging.error(f"Unhandled BadRequestError during invoke: {e}")
                raise
        except Exception as e:
            logging.error(f"An error occurred during invoke: {e}", exc_info=True)
            raise

    def stream(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        messages = [{"role": "user", "content": prompt}]
        try:
            stream = self.client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
            for chunk in stream:
                content_chunk = chunk.choices[0].delta.content
                if content_chunk:
                    yield content_chunk
        except BadRequestError as e:
            if "context length" in str(e).lower() or "too large" in str(e).lower():
                logging.error(f"Prompt exceeded context window for model {self.model}.")
                raise ContextLengthExceededError(f"Prompt is too long for the model's {self.max_context_tokens} token limit.") from e
            else:
                logging.error(f"Unhandled BadRequestError during stream: {e}")
                raise
        except Exception as e:
            logging.error(f"An error occurred during stream: {e}", exc_info=True)
            raise

    def invoke_structured(
        self, prompt: str, response_model: Type[PydanticModel], **kwargs: Any
    ) -> PydanticModel:
        # --- MODIFIED: Use the shared utility function ---
        structured_prompt = build_structured_prompt(prompt, response_model)
        messages = [{"role": "user", "content": structured_prompt}]

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, response_format={"type": "json_object"}, **kwargs
            )
            json_response_str = response.choices[0].message.content
            if not json_response_str:
                raise ValueError("The model returned an empty response.")
            return response_model.model_validate_json(json_response_str)
        except BadRequestError as e:
            if "context length" in str(e).lower() or "too large" in str(e).lower():
                logging.error(f"Prompt exceeded context window for model {self.model}.")
                raise ContextLengthExceededError(f"Prompt is too long for the model's {self.max_context_tokens} token limit.") from e
            else:
                logging.error(f"Unhandled BadRequestError during structured invoke: {e}")
                raise
        except Exception as e:
            logging.error(f"An error occurred during structured invoke: {e}", exc_info=True)
            raise
    

    def invoke_vision_structured(
        self, prompt: str, image_path: Path, response_model: Type[PydanticModel], **kwargs: Any
    ) -> PydanticModel:
        """
        Sends a text prompt and an image to the VLLM and parses a structured JSON response.
        """
        logging.info(f"Performing vision call for image: {image_path.name}")
        base64_image = encode_image_to_base64(image_path)
        
        structured_prompt = build_structured_prompt(prompt, response_model)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": structured_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, response_format={"type": "json_object"}, **kwargs
            )
            json_response_str = response.choices[0].message.content
            if not json_response_str:
                raise ValueError("The vision model returned an empty response.")
            return response_model.model_validate_json(json_response_str)
        except Exception as e:
            logging.error(f"An error occurred during structured vision invoke: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    # --- Pydantic Models for Testing ---
    class NIDInfo(BaseModel):
        name: str = Field(description="The person's full name in Bengali.")
        father_name: str = Field(description="The person's father's name in Bengali.")
        occupation: str = Field(description="The person's occupation in Bengali.")

    class PassportInfo(BaseModel):
        application_type: str = Field(description="The type of passport application, e.g., 'নতুন' (New) or 'নবায়ন' (Renewal).")
        delivery_type: str = Field(description="The delivery speed, e.g., 'জরুরি' (Urgent) or 'সাধারণ' (Regular).")
        validity_years: int = Field(description="The validity period of the passport in years.")


    # --- NEW Pydantic Models for Vision-based Signature Detection ---
    class VLLMSignatureBox(BaseModel):
        box: List[int] = Field(description="A list of 4 integers representing the bounding box in [x1, y1, x2, y2] format.")

    class VLLMSignatureResponse(BaseModel):
        detections: List[VLLMSignatureBox] = Field(description="A list of all detected signatures.")
    
    # --- Setup and Initialization ---
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / ".env")
    # --- Setup and Initialization ---
    print("--- Running Synchronous LLMService Tests ---")
    
    model = os.getenv("LLM_MODEL_NAME")
    base_url = os.getenv("LLM_API_URL")
    api_key=os.getenv("LLM_API_KEY")
    llm_service = None
    if all([model, base_url]):
        llm_service = LLMService(api_key,model, base_url, max_context_tokens=131072 )
    else:
        print("\nWARNING: Small LLM environment variables not set. Skipping tests for small model.")

    # --- NEW TEST: Vision-based Signature Detection ---
    if llm_service:
        print("\n--- Test 4: VLLM - Vision-based Signature Detection ---")
        try:
            # Define the prompt instructing the VLLM what to do
            vision_prompt = "You are a signature detection expert. Analyze the provided image and identify the locations of all handwritten signatures. Provide the bounding box for each signature. The origin (0,0) is the top-left corner of the image."
            
            # Use the same sample image as other tests
            sample_image_path = project_root / "sample_document.png"

            if not sample_image_path.exists():
                print(f"❌ Test Skipped: Sample image 'sample_document.png' not found in project root.")
            else:
                print(f"Prompt: {vision_prompt}")
                print(f"Image: {sample_image_path.name}")
                
                # Call the new vision method
                signature_data = llm_service.invoke_vision_structured(
                    prompt=vision_prompt,
                    image_path=sample_image_path,
                    response_model=VLLMSignatureResponse,
                    temperature=0.0,
                    max_tokens=1024
                )
                
                print("\n✅ Vision Call Successful! Parsed Response:")
                print(signature_data.model_dump_json(indent=2))

        except Exception as e:
            print(f"An error occurred during vision test: {e}")

    # Test 1: Small LLM - Invoke
    if llm_service:
        print("\n--- Test 1: Small LLM - Invoke ---")
        try:
            prompt = "জন্ম নিবন্ধন সনদের গুরুত্ব কী?"
            print(f"Prompt: {prompt}")
            response = llm_service.invoke(prompt, temperature=0.1, max_tokens=256)
            print(f"Response:\n{response}")
        except Exception as e:
            print(f"An error occurred: {e}")

    # Test 2: Small LLM - Stream
    if llm_service:
        print("\n--- Test 2: Small LLM - Stream ---")
        try:
            prompt = "পাসপোর্ট অফিসের একজন কর্মকর্তার একটি সংক্ষিপ্ত বর্ণনা দিন।"
            print(f"Prompt: {prompt}\nStreaming Response:")
            for chunk in llm_service.stream(prompt, temperature=0.2, max_tokens=256):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"An error occurred: {e}")

    # Test 3: Small LLM - Structured Invoke
    if llm_service:
        print("\n--- Test 3: Small LLM - Structured Invoke ---")
        try:
            prompt = "আমার নাম 'করিম চৌধুরী', পিতার নাম 'রহিম চৌধুরী', আমি একজন ছাত্র। এই তথ্য দিয়ে একটি এনআইডি কার্ডের তথ্য তৈরি করুন।"
            print(f"Prompt: {prompt}")
            nid_data = llm_service.invoke_structured(prompt, NIDInfo, temperature=0.0)
            print(f"Parsed Response:\n{nid_data.model_dump_json(indent=2 )}")
        except Exception as e:
            print(f"An error occurred: {e}")
            
    
    print("\n--- All Synchronous Tests Concluded ---")