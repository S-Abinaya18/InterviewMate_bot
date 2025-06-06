import google.generativeai as genai

genai.configure(api_key="AIzaSyDA3dDOmWoJ8vvsDVNJmUjhFZCra3TTSBg")

models = genai.list_models()
for m in models:
    print(m.name)
