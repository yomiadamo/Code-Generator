from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Code Generation Agent is running!"}

class CodeRequest(BaseModel):
    description: str
    auto_run: bool = False

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
    
    # If no code blocks, return the whole text
    return text.strip()

def make_code_non_interactive(code: str, base_filename: str) -> tuple[str, list]:
    """
    Modify code to save matplotlib plots instead of showing them.
    Returns: (modified_code, list_of_output_files)
    """
    output_files = []
    
    # Check if matplotlib is used
    if 'matplotlib' not in code.lower():
        return code, output_files
    
    lines = code.split('\n')
    modified_lines = []
    backend_added = False
    
    for i, line in enumerate(lines):
        # Add non-interactive backend after matplotlib import
        if ('import matplotlib.pyplot' in line or 'from matplotlib' in line) and not backend_added:
            modified_lines.append(line)
            if 'matplotlib.use' not in code:
                modified_lines.append("import matplotlib")
                modified_lines.append("matplotlib.use('Agg')  # Non-interactive backend for saving plots")
                backend_added = True
            continue
        
        # Replace plt.show() with plt.savefig()
        if 'plt.show()' in line:
            indent = len(line) - len(line.lstrip())
            plot_filename = f"{base_filename}_plot.png"
            output_files.append(plot_filename)
            
            save_line = ' ' * indent + f"plt.savefig('{plot_filename}', dpi=300, bbox_inches='tight')"
            print_line = ' ' * indent + f"print('Plot saved as {plot_filename}')"
            
            modified_lines.append(save_line)
            modified_lines.append(print_line)
            continue
        
        modified_lines.append(line)
    
    return '\n'.join(modified_lines), output_files

@app.post("/generate-code")
def generate_code(request: CodeRequest):
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

        # Generate base filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"generated_{timestamp}"
        filename = f"{base_filename}.py"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Post-process code to handle matplotlib
        modified_code, plot_files = make_code_non_interactive(code, base_filename)

        # Save the modified code
        with open(filepath, "w") as f:
            f.write(modified_code)

        result = {
            "raw_response": full_output,
            "extracted_code": code,
            "modified_code": modified_code,
            "saved_to": filepath,
            "expected_plots": plot_files,
            "executed": False
        }

        # Auto-run if requested
        if request.auto_run:
            try:
                # Change to output directory so plots save there
                exec_result = subprocess.run(
                    [sys.executable, filename],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=OUTPUT_DIR
                )
                result["executed"] = True
                result["output"] = exec_result.stdout
                result["errors"] = exec_result.stderr
                result["return_code"] = exec_result.returncode
                
                # Check which plots were actually created
                created_plots = [f for f in plot_files if os.path.exists(os.path.join(OUTPUT_DIR, f))]
                result["created_plots"] = created_plots
                
            except subprocess.TimeoutExpired:
                result["executed"] = True
                result["errors"] = "Execution timed out after 30 seconds"
            except Exception as e:
                result["errors"] = f"Execution error: {str(e)}"

        return result

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/list-generated")
def list_generated_files():
    """List all generated code files and images"""
    files = os.listdir(OUTPUT_DIR)
    
    code_files = [f for f in files if f.endswith('.py')]
    image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    return {
        "code_files": sorted(code_files, reverse=True),
        "image_files": sorted(image_files, reverse=True)
    }

@app.get("/view-code/{filename}")
def view_code(filename: str):
    """View the contents of a generated file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(filepath, "r") as f:
        code = f.read()
    
    return {"filename": filename, "code": code}

@app.get("/view-image/{filename}")
def view_image(filename: str):
    """View generated plot images"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(filepath, media_type="image/png")