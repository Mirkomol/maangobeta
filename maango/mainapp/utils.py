import subprocess
import tempfile

def execute_code(language, code, test_input):
    try:
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py' if language == 'python' else '.js') as temp_code_file:
            temp_code_file.write(code.encode())
            temp_code_path = temp_code_file.name

        # Define the command to execute
        if language == 'python':
            cmd = ['python3', temp_code_path]
        elif language == 'javascript':
            cmd = ['node', temp_code_path]
        else:
            return {"error": "Unsupported language"}

        # Execute the code
        process = subprocess.run(
            cmd,
            input=test_input.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5  # Limit execution time to 5 seconds
        )

        # Return the output or error
        if process.returncode == 0:
            return {"output": process.stdout.strip()}
        else:
            return {"error": process.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"error": "Code execution timed out"}
    except Exception as e:
        return {"error": str(e)}
