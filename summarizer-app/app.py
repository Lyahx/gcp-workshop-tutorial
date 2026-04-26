import os
from flask import Flask, render_template, request, redirect
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def generate(youtube_link, additional_prompt):
    if not additional_prompt:
        additional_prompt = ""
    prompt = f"Please summarize this YouTube video: {youtube_link}\n{additional_prompt}"
    response = model.generate_content(prompt)
    return response.text

@app.route('/summarize', methods=['GET', 'POST'])
def summarize():
    if request.method == 'POST':
        youtube_link = request.form['youtube_link']
        additional_prompt = request.form['additional_prompt']
        try:
            summary = generate(youtube_link, additional_prompt)
            return summary
        except Exception as e:
            return f"Error: {str(e)}", 500
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8080'))
    app.run(debug=False, port=port, host='0.0.0.0')
