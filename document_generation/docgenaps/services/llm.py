import os
import json
import logging
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

class LLMService:
    """
    A synchronous client for OpenAI-compatible APIs using the 'openai' library.
    """
    def __init__(self,model: str, base_url: str, max_context_tokens: int):
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.client = OpenAI(api_key="", base_url=base_url)
        
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

    # --- Setup and Initialization ---
    print("--- Running Synchronous LLMService Tests ---")
    
    model = os.getenv("LLM_MODEL_NAME")
    base_url = os.getenv("LLM_API_URL")
    llm_service = None
    if all([model, base_url]):
        llm_service = LLMService(model, base_url, max_context_tokens=131072 )
    else:
        print("\nWARNING: Small LLM environment variables not set. Skipping tests for small model.")

    
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