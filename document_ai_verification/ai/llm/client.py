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
            logging.error(f"An error occurred during structured vision invoke: {e}  value: {json_response_str}", exc_info=True)
            raise
    
    def invoke_image_compare_structured(
        self, prompt: str, image_path_1: Path, image_path_2: Path, response_model: Type[PydanticModel], **kwargs: Any
    ) -> PydanticModel:
        """
        Sends a text prompt and two images to the VLLM for comparison and parses a structured JSON response.

        Args:
            prompt (str): The text prompt describing the comparison task.
            image_path_1 (Path): Path to the first image file.
            image_path_2 (Path): Path to the second image file.
            response_model (Type[PydanticModel]): The Pydantic model to structure the response.
            **kwargs: Additional arguments to pass to the API (e.g., temperature, max_tokens).

        Returns:
            PydanticModel: The parsed response conforming to the specified model.

        Raises:
            ValueError: If the model returns an empty response.
            ContextLengthExceededError: If the prompt exceeds the model's context window.
            Exception: For other API or processing errors.
        """
        logging.info(f"Performing vision-based comparison for images: {image_path_1.name} and {image_path_2.name}")
        
        # Encode both images to base64
        base64_image_1 = encode_image_to_base64(image_path_1)
        base64_image_2 = encode_image_to_base64(image_path_2)
        
        # Build the structured prompt
        structured_prompt = build_structured_prompt(prompt, response_model)
        
        # Construct the message with text prompt and two images
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": structured_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image_1}"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image_2}"},
                    },
                ],
            }
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model, 
                messages=messages, 
                response_format={"type": "json_object"}, 
                **kwargs
            )
            json_response_str = response.choices[0].message.content
            if not json_response_str:
                raise ValueError("The vision model returned an empty response.")
            return response_model.model_validate_json(json_response_str)
        except BadRequestError as e:
            if "context length" in str(e).lower() or "too large" in str(e).lower():
                logging.error(f"Prompt exceeded context window for model {self.model}.")
                raise ContextLengthExceededError(
                    f"Prompt is too long for the model's {self.max_context_tokens} token limit."
                ) from e
            else:
                logging.error(f"Unhandled BadRequestError during structured image comparison invoke: {e}")
                raise
        except Exception as e:
            logging.error(f"An error occurred during structured image comparison invoke: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    # --- Setup and Initialization ---
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / ".env")
    # Use the same sample image as other tests
    sample_image_path = project_root / "sample_document.png"

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

    