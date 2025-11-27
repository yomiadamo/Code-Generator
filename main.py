from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import requests
import re
import os
from datetime import datetime
import subprocess
import sys

app = FastAPI()

# Directory to save generated code
OUTPUT_DIR = "generated_code"
os.makedirs(OUTPUT_DIR, exist_ok=True) # Creates directory if it doesn't already exists

@app.get("/")
def root():
    return {"message": "Code Generation Agent is running!"}

class CodeRequest(BaseModel):
    description: str
    auto_run: bool = False # Safety flag

def extract_python_code(text: str) -> str:
    """Extract Python code from markdown code blocks or raw text"""
    # Try to find code in markdown blocks first
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # Try without language specifier
    pattern = r"```\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    
    # If no code blocks, return the whole text (assumes it's all code)
    return text.strip()

@app.post("/generate-code")
def generate_code(request: CodeRequest):
    # Enhanced prompt for better code generation
    prompt = f"""You are a Python code generator. Generate clean, working Python code for the following request:

{request.description}

Requirements:
- Write only the Python code, nothing else
- Include necessary imports
- Add brief comments for clarity
- Make sure the code is complete and runnable

Python code:"""

    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt,
        "stream": True
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            stream=True,
            timeout=60
        )
        response.raise_for_status()

        full_output = ""
        for line in response.iter_lines():
            if line:
                obj = json.loads(line.decode("utf-8"))
                full_output += obj.get("response", "")

        # Extract the actual code
        code = extract_python_code(full_output)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_{timestamp}.py"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Save the code
        with open(filepath, "w") as f:
            f.write(code)

        result = {
            "raw_response": full_output,
            "extracted_code": code,
            "saved_to": filepath,
            "executed": False
        }

        # Auto-run if requested
        if request.auto_run:
            try:
                exec_result = subprocess.run(
                    [sys.executable, filepath],
                    capture_output=True,
                    text=True,
                    timeout=10  # 10 second timeout for safety
                )
                result["executed"] = True
                result["output"] = exec_result.stdout
                result["errors"] = exec_result.stderr
                result["return_code"] = exec_result.returncode
            except subprocess.TimeoutExpired:
                result["executed"] = True
                result["errors"] = "Execution timed out after 10 seconds"
            except Exception as e:
                result["errors"] = f"Execution error: {str(e)}"

        return result

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")