import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="Gemma 4 World Cup Analyst API",
    description="Production-grade API demonstrating Gemma 4's Thinking Mode and Structured Output.",
    version="1.0.0"
)

# Default configurations
DEFAULT_CLOUD_MODEL = "gemini-2.5-flash"
DEFAULT_LOCAL_MODEL = "gemma4:12b"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
GEMINI_STREAM_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={key}&alt=sse"

class AnalysisRequest(BaseModel):
    scenario: str
    local: bool = False
    model: str = None

JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "commentator_script": {
            "type": "STRING",
            "description": "High energy play-by-play commentary script describing the run-up, shot, and outcome."
        },
        "tactical_breakdown": {
            "type": "STRING",
            "description": "A technical, data-oriented breakdown of why the shooter/goalkeeper succeeded or failed."
        },
        "excitement_index": {
            "type": "INTEGER",
            "description": "An excitement score from 1 to 10 based on the drama of the moment."
        }
    },
    "required": ["commentator_script", "tactical_breakdown", "excitement_index"]
}

def get_cloud_payload(prompt):
    return {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": JSON_SCHEMA,
            "thinkingConfig": {
                "thinkingBudget": 2048
            }
        }
    }

def get_local_payload(model, scenario):
    prompt = (
        f"Analyze this high-stakes World Cup match scenario:\n\n{scenario}\n\n"
        "Instructions:\n"
        "1. You MUST first think about the scenario. Write your thinking process wrapped in <|think|> and </|think|> tags.\n"
        "2. After the closing </|think|> tag, you MUST output a JSON object matching this schema:\n"
        "{\n"
        "  \"commentator_script\": \"High energy play-by-play commentary script describing the run-up, shot, and outcome.\",\n"
        "  \"tactical_breakdown\": \"A technical, data-oriented breakdown of why the shooter/goalkeeper succeeded or failed.\",\n"
        "  \"excitement_index\": 9\n"
        "}\n"
        "Do not output any other text before or after the JSON."
    )
    return {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Gemma 4 World Cup Analyst API"}

@app.post("/analyze")
def analyze_scenario(req: AnalysisRequest):
    """
    Standard HTTP endpoint that returns the final parsed JSON from the model.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. Determine Local vs Cloud Mode
    if req.local or not api_key:
        # Local Mode
        model_name = req.model or os.environ.get("LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        payload = get_local_payload(model_name, req.scenario)
        
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
        
        try:
            with urllib.request.urlopen(request) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                raw_text = res_data.get("response", "")
                
                # Extract JSON block after thinking tags
                json_part = raw_text
                if "</|think>" in raw_text:
                    json_part = raw_text.split("</|think>")[1].strip()
                elif "</think>" in raw_text:
                    json_part = raw_text.split("</think>")[1].strip()
                
                if "```json" in json_part:
                    json_part = json_part.split("```json")[1].split("```")[0].strip()
                elif "```" in json_part:
                    json_part = json_part.split("```")[1].split("```")[0].strip()
                
                return json.loads(json_part)
        except urllib.error.URLError as e:
            raise HTTPException(status_code=503, detail=f"Local Ollama connection failed: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing local model output: {e}")
            
    else:
        # Cloud Mode
        model_name = req.model or os.environ.get("GEMINI_MODEL", DEFAULT_CLOUD_MODEL)
        url = GEMINI_URL_TEMPLATE.format(model=model_name, key=api_key)
        
        prompt = (
            f"Analyze this high-stakes World Cup match scenario:\n\n{req.scenario}\n\n"
            "Using your reasoning capabilities, evaluate: "
            "1. The psychological pressure on both the shooter and goalkeeper. "
            "2. The tactical shootout history and placement strategy. "
            "3. How to write a high-energy play-by-play commentary script. "
            "Provide your final answer as a JSON object matching the requested schema."
        )
        
        payload = get_cloud_payload(prompt)
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        
        try:
            with urllib.request.urlopen(request) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if not candidates:
                    raise HTTPException(status_code=500, detail="No response candidate returned from Gemini API.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                # The final structured output is in the non-thought text part
                for part in parts:
                    if not part.get("thought", False):
                        return json.loads(part.get("text", "{}"))
                raise HTTPException(status_code=500, detail="No structured output part found in the model response.")
        except urllib.error.HTTPError as e:
            raise HTTPException(status_code=e.code, detail=f"Gemini API returned error: {e.read().decode('utf-8')}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.post("/analyze/stream")
def analyze_scenario_stream(req: AnalysisRequest):
    """
    Streaming endpoint that streams raw model thoughts and final JSON back to the client.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Simple generator to yield data chunks
    def cloud_stream_generator(model_name, key):
        prompt = (
            f"Analyze this high-stakes World Cup match scenario:\n\n{req.scenario}\n\n"
            "Using your reasoning capabilities, evaluate: "
            "1. The psychological pressure on both the shooter and goalkeeper. "
            "2. The tactical shootout history and placement strategy. "
            "3. How to write a high-energy play-by-play commentary script. "
            "Provide your final answer as a JSON object matching the requested schema."
        )
        payload = get_cloud_payload(prompt)
        url = GEMINI_STREAM_URL_TEMPLATE.format(model=model_name, key=key)
        
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            response = urllib.request.urlopen(request)
            for line in response:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data:"):
                    yield line_str + "\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n"

    def local_stream_generator(model_name):
        prompt = (
            f"Analyze this high-stakes World Cup match scenario:\n\n{req.scenario}\n\n"
            "Instructions:\n"
            "1. You MUST first think about the scenario. Write your thinking process wrapped in <|think|> and </|think|> tags.\n"
            "2. After the closing </|think|> tag, you MUST output a JSON object matching this schema:\n"
            "{\n"
            "  \"commentator_script\": \"High energy play-by-play commentary script describing the run-up, shot, and outcome.\",\n"
            "  \"tactical_breakdown\": \"A technical, data-oriented breakdown of why the shooter/goalkeeper succeeded or failed.\",\n"
            "  \"excitement_index\": 9\n"
            "}\n"
            "Do not output any other text before or after the JSON."
        )
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True
        }
        headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            response = urllib.request.urlopen(request)
            for line in response:
                yield line.decode("utf-8")
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    if req.local or not api_key:
        model_name = req.model or os.environ.get("LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        return StreamingResponse(local_stream_generator(model_name), media_type="text/event-stream")
    else:
        model_name = req.model or os.environ.get("GEMINI_MODEL", DEFAULT_CLOUD_MODEL)
        return StreamingResponse(cloud_stream_generator(model_name, api_key), media_type="text/event-stream")
