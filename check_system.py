
import os
import requests
import sys
from dotenv import load_dotenv
load_dotenv()

def check_ollama():
    print("\n--- Checking Ollama ---")
    try:
        response = requests.get("http://localhost:11434")
        if response.status_code == 200:
            print("✅ Ollama is running!")
            return True
        else:
            print(f"❌ Ollama returned status: {response.status_code}")
    except Exception as e:
        print("❌ Ollama is NOT running or not accessible.")
        print(f"Error: {e}")
        print("To fix: Install Ollama from https://ollama.com and run 'ollama serve'")
    return False

if __name__ == "__main__":
    check_ollama()