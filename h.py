import google.generativeai as genai

# 1. Setup your API Key
# Best practice: replace "YOUR_API_KEY" with your actual string
genai.configure(api_key="AIzaSyDPrw7guA7-J69W-mFGy5OY4UD6Wuopo1E")

# 2. Fix the 404 error: Use the versioned model name or the latest alias
# Try 'gemini-1.5-flash' first. If that 404s, use 'gemini-1.5-flash-latest'
model_name = 'gemma-3-1b-it' 

try:
    print(f"Attempting to connect to {model_name}...")
    
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("capital of dubai")
    
    print("-" * 30)
    print("RESULT:", response.text)
    print("-" * 30)

except Exception as e:
    # This will tell us if the model name is wrong or the API key is invalid
    print(f"\n[ERROR]: {e}")
    
    # Troubleshooting: List all models available to your specific API key
    print("\nListing models available to your key:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")