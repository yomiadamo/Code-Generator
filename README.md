# Math-App
Author: Yomi Adamo

Hello, this was a test to see how how well the Llama 3.2 3B model worked with generating runnable python code, as well as storing the code and automatically running it.

## How To Use
1. Install Ollama Model
~~~bash
curl -fsSL https://ollama.com/install.sh | sh
~~~

2. Pull Llama 3.2 3B model
~~~bash
ollama pull llama3.2:3B
~~~

3. Clone the directory
~~~bash
git clone https://github.com/yomi-adamo/Code-Generator.git

cd Code-Generator
~~~

4. Create virtual environment 
~~~bash
python3 -m venv venv
~~~

5. Activate the virtual environmet and install dependencies
~~~bash
source venv/bin/activate

pip install fastapi uvicorn requests
~~~

6. Run the code
~~~bash
uvicorn main:app --reload
~~~

7. Example
~~~bash
curl -X POST http://localhost:8000/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Create a Python script that generates a sine wave and plots it using matplotlib. The wave should have a frequency of 5 Hz, be sampled at 100 Hz, and show 2 seconds of data.",
    "auto_run": true
  }'
~~~

8. Find code and plot image
~~~bash
cd generated_code
~~~

9. Open Image
~~~bash
eog <image file>
~~~