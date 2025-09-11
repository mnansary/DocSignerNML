Of course. Crafting professional, detailed, and machine-readable documentation is a critical step. An AI coding agent or a new developer should be able to look at this document and immediately understand how to interact with your API.

Here is the complete documentation for your three primary API services, written in a structured Markdown format that is easy to parse.

***

# Apsis Solutions API Gateway Documentation v1.8

## Overview

This document provides detailed specifications for the Apsis Solutions API Gateway. The gateway serves as a unified entry point for a suite of backend microservices, including signature detection, multilingual OCR, and direct access to a powerful Gemma-3 Large Language Model.

**Base URL:** `http://myapi.com/`

**Authentication:** All endpoints are currently public and do not require an authentication token.

---

## 1. Signature Detection

This service utilizes a high-performance YOLOv8 ensemble model deployed on a Triton Inference Server to detect handwritten signatures in an image. It is optimized for low-latency, high-throughput scenarios.

*   **Endpoint:** `POST /signdet`
*   **Full URL:** `http://myapi.com/signdet`

### Description

Upload an image containing documents or forms. The service will analyze the image and return a list of bounding boxes, each corresponding to a detected signature, along with a confidence score for each detection.

### Request

The request must be sent as `multipart/form-data`.

**Query Parameters:**

| Parameter            | Type    | Required | Default | Description                                                                  |
| -------------------- | ------- | -------- | ------- | ---------------------------------------------------------------------------- |
| `confidence`         | `float` | No       | `0.5`   | The confidence threshold (0.0 to 1.0) for a detection to be considered valid. |
| `iou`                | `float` | No       | `0.45`  | The Intersection over Union (IoU) threshold for non-maximum suppression.     |

**Body:**

| Key    | Type   | Required | Description                                     |
| ------ | ------ | -------- | ----------------------------------------------- |
| `file` | `file` | Yes      | The image file to be processed (e.g., PNG, JPG). |

### Response

**Success (`200 OK`):**

The response is a JSON object containing the results of the detection.

**Response Body Schema:**

*   `request_id` (string): A unique identifier for this specific request.
*   `detection_count` (integer): The total number of signatures found.
*   `detections` (List[Object]): A list of detection objects.
    *   `box` (List[float]): A list of 4 floating-point numbers representing the bounding box in `[x1, y1, x2, y2]` format.
    *   `confidence` (float): The model's confidence score for the detection, from 0.0 to 1.0.

**Sample Response:**
```json
{
    "request_id": "eeb06ecc-2aa1-4056-ab7e-1db56cab3c95",
    "detections": [
        {
            "box": [
                26.88,
                265.5,
                249.0,
                188.88
            ],
            "confidence": 0.6777
        },
        {
            "box": [
                346.0,
                50.59,
                207.0,
                141.12
            ],
            "confidence": 0.5508
        }
    ],
    "detection_count": 2
}
```

**Error Responses:**

*   `503 Service Unavailable`: The backend Triton server is unreachable or failed to process the request.

### Code Example (cURL)

```bash
curl -X POST "http://myapi.com/signdet?confidence=0.5&iou=0.45" \
-F "file=@/path/to/your/document_with_signature.png"
```

---

## 2. English Optical Character Recognition (enOCR)

This endpoint provides a robust, high-accuracy OCR service specifically optimized for extracting English text from document images. It acts as a proxy to a dedicated OCR microservice.

*   **Endpoint:** `POST /enocr`
*   **Full URL:** `http://myapi.com/enocr`

### Description

Upload a document image containing English text. The service returns a detailed JSON object containing the transcribed text, line-by-line data with bounding polygons, and a plain text version of the full document.

### Request

The request must be sent as `multipart/form-data`.

**Body:**

| Key    | Type   | Required | Description                                     |
| ------ | ------ | -------- | ----------------------------------------------- |
| `file` | `file` | Yes      | The image file to be processed (e.g., PNG, JPG). |

### Response

**Success (`200 OK`):**

The response is a JSON object containing the full OCR result.

**Response Body Schema:**

*   `status` (string): Will be `"success"` if the OCR operation was completed.
*   `plain_text` (string): The full extracted text with newline characters `\n` preserving the document's line breaks.
*   `detailed_data` (List[Object]): A list of word/phrase objects, each containing detailed information.
    *   `poly` (List[integer]): A list of 8 integers representing the four corner points `[x1, y1, x2, y2, x3, y3, x4, y4]` of the bounding polygon around the text.
    *   `text` (string): The transcribed text for that specific polygon.
    *   `line_num` (integer): The line number the text belongs to in the document.
    *   `word_num` (integer): The word number within that specific line.

**Sample Response:**
```json
{
    "detailed_data": [
        {
            "poly": [284, 45, 361, 45, 361, 63, 284, 63],
            "text": "Abstract",
            "line_num": 1,
            "word_num": 1
        },
        {
            "poly": [52, 88, 591, 88, 591, 102, 52, 102],
            "text": "Traditional OCR systems (OCR-1.0) are increasingly unable to meet people's",
            "line_num": 2,
            "word_num": 1
        }
    ],
    "plain_text": "Abstract\nTraditional OCR systems (OCR-1.0) are increasingly unable to meet people's\n...",
    "status": "success"
}
```

**Error Responses:**

*   `502 Bad Gateway`: The dedicated enOCR microservice is unavailable.

### Code Example (cURL)

```bash
curl -X POST "http://myapi.com/enocr" \
-F "file=@/path/to/your/english_document.png"
```
---

## 3. Gemma-3 Language Model Gateway

This endpoint provides direct, proxied access to a backend Gemma-3 Large Language Model served via vLLM. The gateway exposes the OpenAI-compatible API, allowing for seamless integration with existing tools and SDKs. This documentation covers the **non-streaming** chat completions endpoint.

*   **Endpoint:** `POST /gemma3/{full_path:path}`
*   **Example Full URL:** `http://myapi.com/gemma3/v1/chat/completions`

### Description

This is a full reverse proxy. It forwards any request made to `/apsis/gemma3/` directly to the backend vLLM server. You can use any valid OpenAI-compatible API path and payload. This is ideal for tasks requiring advanced reasoning, text generation, or structured data extraction. The vLLM backend supports guided JSON output via the `response_format` parameter.

### Request

The request must be sent as `application/json`. The body should conform to the OpenAI Chat Completions API specification.

**Body Schema (Common Parameters):**

*   `model` (string, required): The name of the model to use (e.g., `"RedHatAI/gemma-3-27b-it-quantized.w8a8"`).
*   `messages` (List[Object], required): A list of message objects.
    *   `role` (string): The role of the message author (e.g., `"system"`, `"user"`).
    *   `content` (string | List[Object]): The message content. For vision tasks, this is a list of image and text objects.
*   `max_tokens` (integer, optional): The maximum number of tokens to generate.
*   `temperature` (float, optional): Controls randomness. A value of `0.0` is deterministic.
*   `response_format` (Object, optional): Used for guided JSON output. Example: `{"type": "json_object"}`.

### Response

**Success (`200 OK`):**

The response is a direct passthrough from the backend vLLM server and conforms to the OpenAI Chat Completions API specification.

**Response Body Schema:**

*   `id` (string): A unique identifier for the completion.
*   `object` (string): The object type, typically `"chat.completion"`.
*   `created` (integer): The Unix timestamp of when the completion was created.
*   `model` (string): The model used for the completion.
*   `choices` (List[Object]): A list of completion choices (usually one).
    *   `index` (integer): The index of the choice.
    *   `message` (Object): The message object generated by the model.
        *   `role` (string): Always `"assistant"`.
        *   `content` (string): The text of the generated response.
    *   `finish_reason` (string): The reason the model stopped generating (e.g., `"stop"`, `"length"`).
*   `usage` (Object): An object detailing the token usage for the request.
    *   `prompt_tokens` (integer): Tokens in the input prompt.
    *   `completion_tokens` (integer): Tokens in the generated response.
    *   `total_tokens` (integer): The sum of prompt and completion tokens.

**Sample Response:**
```json
{
    "id": "chatcmpl-05f4d9244d4c4fee97bb3f646f632ac6",
    "object": "chat.completion",
    "created": 1757324284,
    "model": "RedHatAI/gemma-3-27b-it-quantized.w8a8",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Okay, here are the three main benefits of using a reverse proxy..."
            },
            "finish_reason": "length"
        }
    ],
    "usage": {
        "prompt_tokens": 26,
        "total_tokens": 226,
        "completion_tokens": 200
    }
}
```

### Code Example (cURL)

```bash
curl -X POST "http://myapi.com/gemma3/v1/chat/completions" \
-H "Content-Type: application/json" \
-d '{
  "model": "RedHatAI/gemma-3-27b-it-quantized.w8a8",
  "messages": [
    {
      "role": "user",
      "content": "What are the three main benefits of using a reverse proxy in a microservice architecture?"
    }
  ],
  "max_tokens": 200,
  "temperature": 0.7
}'
```