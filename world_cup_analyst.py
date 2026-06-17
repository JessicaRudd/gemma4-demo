#!/usr/bin/env python3
"""
Gemma 4 World Cup Live Demo Analyst - Interactive Edition
Demonstrates Thinking Mode and Structured Outputs (JSON Schema) in a live demo.
Supports both Google AI Studio (Cloud) and Ollama (Local) as a robust presentation safety net.
Allows interactive selection of preset scenarios or typing custom audience suggestions live.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

# ANSI Color Codes for terminal beauty
COLOR_HEADER = "\033[95m"    # Purple
COLOR_THINK = "\033[93m"     # Yellow/Orange
COLOR_JSON = "\033[96m"      # Cyan
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"

# Default configurations
DEFAULT_CLOUD_MODEL = "gemini-2.5-flash"
DEFAULT_LOCAL_MODEL = "gemma4:12b"
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={key}&alt=sse"

# Preset Scenarios
PRESETS = {
    "1": {
        "title": "USA vs Canada (2026 Deciding Penalty Shootout)",
        "description": (
            "Match: Quarter-Finals, USA vs Canada (2026 FIFA World Cup). "
            "Time: Deciding penalty in the shootout. "
            "Score is currently tied at 4-4 in penalties. "
            "Shooter: Christian Pulisic (USA Captain). "
            "Goalkeeper: Maxime Crépeau (Canada). "
            "Details: If Pulisic scores, USA wins and advances to the semi-finals. "
            "If Crépeau saves it, sudden death continues. The stadium of 65,000 in Toronto is deafening. "
            "Pulisic has historical tendencies to go low-right under pressure, but Crépeau is known for late, explosive dives."
        )
    },
    "2": {
        "title": "Argentina vs France (2022 World Cup Final)",
        "description": (
            "Match: World Cup Final, Argentina vs France. "
            "Time: Penalty shootout. "
            "Score in shootout is tied 2-2. "
            "Shooter: Lionel Messi (Argentina Captain). "
            "Goalkeeper: Hugo Lloris (France). "
            "Details: The legendary stadium of Lusail is packed with 88,000 people. "
            "Messi steps up with immense weight on his shoulders. Lloris is a veteran keeper, but "
            "Messi has a history of stutter-step run-ups to freeze the keeper before placing it coolly."
        )
    }
}

# JSON Schema for Structured Output
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

def get_scenario_interactively():
    print(f"{COLOR_HEADER}=== Select Match Scenario ==={COLOR_RESET}")
    print("  [1] USA vs Canada (2026 Shootout - Pulisic vs Crépeau)")
    print("  [2] Argentina vs France (2022 Final - Messi vs Lloris)")
    print("  [3] Custom Scenario (Type your own live based on audience suggestions!)")
    
    choice = input(f"\nSelect scenario [1-3] (Default: 1): ").strip()
    if not choice:
        choice = "1"
        
    if choice in PRESETS:
        selected = PRESETS[choice]
        print(f"\nSelected: {COLOR_GREEN}{selected['title']}{COLOR_RESET}")
        return selected["description"]
    elif choice == "3":
        print(f"\n{COLOR_HEADER}--- Enter Custom Scenario Details ---{COLOR_RESET}")
        print("Tip: Describe the Teams, Player, Situation, and Goalkeeper:")
        custom_input = input("> ").strip()
        if not custom_input:
            print(f"{COLOR_RED}Empty input. Falling back to default scenario.{COLOR_RESET}")
            return PRESETS["1"]["description"]
        return custom_input
    else:
        print(f"{COLOR_RED}Invalid choice. Falling back to default scenario.{COLOR_RESET}")
        return PRESETS["1"]["description"]


def run_cloud_demo(model, api_key, scenario):
    print(f"\nMode: {COLOR_GREEN}Cloud (Google AI Studio){COLOR_RESET}")
    print(f"Model: {COLOR_GREEN}{model}{COLOR_RESET}\n")

    prompt = (
        f"Analyze this high-stakes World Cup match scenario:\n\n{scenario}\n\n"
        "Using your reasoning capabilities, evaluate: "
        "1. The psychological pressure on both the shooter and goalkeeper. "
        "2. The tactical shootout history and placement strategy. "
        "3. How to write a high-energy play-by-play commentary script. "
        "Provide your final answer as a JSON object matching the requested schema."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": JSON_SCHEMA,
            "thinkingConfig": {
                "thinkingBudget": 2048
            }
        }
    }

    url = GEMINI_URL_TEMPLATE.format(model=model, key=api_key)
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)

    print(f"{COLOR_HEADER}--- 1. STARTING THINKING STREAM (Cloud Reasoning) ---{COLOR_RESET}")
    print(f"{COLOR_THINK}", end="", flush=True)

    final_json_buffer = []
    is_thinking = True
    
    try:
        response = urllib.request.urlopen(req)
        for line in response:
            line_str = line.decode("utf-8").strip()
            if not line_str.startswith("data:"):
                continue
            
            json_str = line_str[5:].strip()
            if not json_str:
                continue
            
            try:
                chunk = json.loads(json_str)
            except Exception:
                continue
            
            candidates = chunk.get("candidates", [])
            if not candidates:
                continue
            
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                text = part.get("text", "")
                chunk_is_thought = part.get("thought", False)
                
                if chunk_is_thought:
                    if not is_thinking:
                        is_thinking = True
                        print(f"\n{COLOR_THINK}", end="", flush=True)
                    sys.stdout.write(text)
                    sys.stdout.flush()
                else:
                    if is_thinking:
                        is_thinking = False
                        print(f"{COLOR_RESET}\n")
                        print(f"{COLOR_HEADER}--- 2. FINAL STRUCTURED OUTPUT (JSON Schema) ---{COLOR_RESET}")
                        print(f"{COLOR_JSON}", end="", flush=True)
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    final_json_buffer.append(text)
                    
        print(f"{COLOR_RESET}\n")
        print(f"{COLOR_HEADER}--- 3. DEMO SUMMARY ---{COLOR_RESET}")
        print("✓ Successfully executed model reasoning stream (Thinking Mode)")
        print("✓ Enforced strict JSON output using responseSchema constraints")
        
        full_json = "".join(final_json_buffer).strip()
        print_parsed_details(full_json)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"\n{COLOR_RED}HTTP Error {e.code}: {error_body}{COLOR_RESET}")
        if e.code == 503:
            print(f"\n{COLOR_THINK}Tip: Server busy. You can run the local backup using:{COLOR_RESET}")
            print(f"  {sys.argv[0]} --local")
    except Exception as e:
        print(f"\n{COLOR_RED}Error running cloud demo: {e}{COLOR_RESET}")


def run_local_demo(model, scenario):
    print(f"\nMode: {COLOR_GREEN}Local (Ollama Backup){COLOR_RESET}")
    print(f"Model: {COLOR_GREEN}{model}{COLOR_RESET}\n")

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

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)

    print(f"{COLOR_HEADER}--- 1. STARTING THINKING STREAM (Local Reasoning) ---{COLOR_RESET}")
    print(f"{COLOR_THINK}", end="", flush=True)

    final_json_buffer = []
    in_thoughts = True
    
    try:
        response = urllib.request.urlopen(req)
        for line in response:
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            
            try:
                chunk = json.loads(line_str)
            except Exception:
                continue
            
            text = chunk.get("response", "")
            
            # Simple streaming parser to highlight thoughts vs final JSON
            if "<|think>" in text or "<think>" in text:
                in_thoughts = True
                sys.stdout.write(text)
                sys.stdout.flush()
                continue
            
            if "</|think>" in text or "</think>" in text:
                in_thoughts = False
                sys.stdout.write(text)
                sys.stdout.write(f"{COLOR_RESET}\n\n")
                print(f"{COLOR_HEADER}--- 2. FINAL STRUCTURED OUTPUT (JSON Schema) ---{COLOR_RESET}")
                print(f"{COLOR_JSON}", end="", flush=True)
                continue
                
            sys.stdout.write(text)
            sys.stdout.flush()
            if not in_thoughts:
                final_json_buffer.append(text)
                
        print(f"{COLOR_RESET}\n")
        print(f"{COLOR_HEADER}--- 3. DEMO SUMMARY ---{COLOR_RESET}")
        print("✓ Successfully executed local model stream (Thinking Mode)")
        print("✓ Extracted JSON output from prompt-constrained local weights")
        
        full_json = "".join(final_json_buffer).strip()
        if "```json" in full_json:
            full_json = full_json.split("```json")[1].split("```")[0].strip()
        elif "```" in full_json:
            full_json = full_json.split("```")[1].split("```")[0].strip()
            
        print_parsed_details(full_json)

    except urllib.error.URLError as e:
        print(f"\n{COLOR_RED}Connection Error: Could not reach Ollama at {OLLAMA_URL}.{COLOR_RESET}")
        print("Please ensure Ollama is running locally and the model is downloaded:")
        print(f"  ollama run {model}\n")
    except Exception as e:
        print(f"\n{COLOR_RED}Error running local demo: {e}{COLOR_RESET}")


def print_parsed_details(full_json):
    if not full_json:
        return
    try:
        start_idx = full_json.find('{')
        end_idx = full_json.rfind('}')
        if start_idx != -1 and end_idx != -1:
            full_json = full_json[start_idx:end_idx+1]
            
        parsed = json.loads(full_json)
        print(f"\nParsed Result Details:")
        print(f"  - Excitement Index: {COLOR_GREEN}{parsed.get('excitement_index')}/10{COLOR_RESET}")
        print(f"  - Commentary Length: {len(parsed.get('commentator_script', ''))} chars")
        print(f"  - Tactical Breakdown: {parsed.get('tactical_breakdown')[:120]}...")
    except Exception as e:
        print(f"\nCould not parse final JSON block: {e}")
        print(f"Raw Output: {full_json[:200]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemma 4 World Cup Live Demo Analyst")
    parser.add_argument("--local", "-l", action="store_true", help="Run locally using Ollama")
    parser.add_argument("--model", "-m", type=str, help="Override model name")
    args = parser.parse_args()

    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 1. Print header
    print(f"{COLOR_HEADER}=== Gemma 4 / Gemini World Cup Analyst Live Demo ==={COLOR_RESET}\n")
    
    # 2. Get scenario interactively
    scenario = get_scenario_interactively()
    
    # 3. Execute demo
    if args.local or not api_key:
        model = args.model or os.environ.get("LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        run_local_demo(model, scenario)
    else:
        model = args.model or os.environ.get("GEMINI_MODEL", DEFAULT_CLOUD_MODEL)
        run_cloud_demo(model, api_key, scenario)
