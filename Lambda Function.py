import json
import subprocess

def lambda_handler(event, context):
    try:
        process = subprocess.run(["python", "Python file.py"], capture_output=True, text=True)

        output = process.stdout
        error = process.stderr

        if process.returncode == 0:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Script executed successfully", "output": output})
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Script execution failed", "error": error})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Lambda function failed", "error": str(e)})
        }
