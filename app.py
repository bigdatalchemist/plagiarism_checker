# app.py
from flask import Flask, render_template, request
from utils.similarity import compare_texts
from utils.utils import extract_text_from_file
from utils.webscraper import extract_text_from_url
from config import SYSTEM_PAGE_LIMIT
import os
import nltk
from api import api

# Ensure punkt is downloaded silently
nltk.download('punkt', quiet=True)

app = Flask(__name__)
app.register_blueprint(api)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    mode = 'text'
    selected_indexes1 = selected_indexes2 = []
    input_text1 = input_text2 = ""
    form_data = {"text1": "", "text2": "", "url1": "", "url2": "", "pages": 1}
    uploaded_files = {"file1": None, "file2": None}

    if request.method == 'POST':
        mode = request.form.get('mode')
        form_data['pages'] = int(request.form.get('pages', 1))

        if mode == 'text':
            form_data['text1'] = request.form.get('text1', '')
            form_data['text2'] = request.form.get('text2', '')
            input_text1 = form_data['text1']
            input_text2 = form_data['text2']
            result = compare_texts(input_text1, input_text2)

        elif mode == 'file':
            file1 = request.files.get('file1')
            file2 = request.files.get('file2')
            pages = form_data['pages']
            if file1 and file2:
                text1, _, selected_indexes1 = extract_text_from_file(file1, pages)
                text2, _, selected_indexes2 = extract_text_from_file(file2, pages)

                # Store the file paths for later display
                uploaded_files["file1"] = file1.filename
                uploaded_files["file2"] = file2.filename

                # PRINT OUT EXTRACTED TEXT FOR DEBUGGING
                print("Extracted Text 1:", text1)
                print("Extracted Text 2:", text2)
                
                # After printing, check if the text is too short:
                if len(text1.strip()) < 20:
                    print("Text1 is too short!")
                if len(text2.strip()) < 20:
                    print("Text2 is too short!")

                input_text1 = text1
                input_text2 = text2

                if not text1.strip() or not text2.strip():
                    result = {"word_score": 0.0,
                               "similar_words": [], 
                               "semantic_score": 0.0, 
                               "paraphrased_phrases": ["No readable content found."]}
                else:
                    result = compare_texts(text1, text2)

        elif mode == 'url':
            form_data['url1'] = request.form.get('url1', '')
            form_data['url2'] = request.form.get('url2', '')

            text1 = extract_text_from_url(form_data['url1'])
            text2 = extract_text_from_url(form_data['url2'])
            input_text1 = text1
            input_text2 = text2

            if not text1.strip() or not text2.strip():
                result = {"word_score": 0.0,
                           "similar_words": [], 
                           "semantic_score": 0.0, 
                           "paraphrased_phrases": ["No readable content found."]}
            else:
                result = compare_texts(text1, text2)

    return render_template(
        'index.html',
        form_data=form_data,
        mode=mode,
        result=result,
        input_text1=input_text1,
        input_text2=input_text2,
        selected_indexes1=selected_indexes1,
        selected_indexes2=selected_indexes2,
        uploaded_files=uploaded_files,
        page_limit=SYSTEM_PAGE_LIMIT
    )

if __name__ == '__main__':
    app.run(debug=True)
