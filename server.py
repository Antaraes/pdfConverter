from flask import Flask, request, jsonify
import fitz
import os
import zlib
import base64
import json
import tempfile

import os
from supabase import create_client, Client

url: str = "https://mzesvrtnjyoqhqbwrxob.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16ZXN2cnRuanlvcWhxYndyeG9iIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTgwMzUyMjMsImV4cCI6MjAxMzYxMTIyM30._DCwMToNZwT96w5t_Nn63S1mT6cuLARN7p7Abq67aBo"
supabase: Client = create_client(url, key)
app = Flask(__name__)


def compress_content(content):
    compressed_content = zlib.compress(json.dumps(content).encode('utf-8'))
    compressed_base64 = base64.b64encode(compressed_content).decode('utf-8')
    return compressed_base64


def compress_content_entries(content_entries):
    compressed_entries = []
    for entry in content_entries:
        compressed_content = compress_content(entry['content'])
        compressed_entry = {
            "bookId": entry["bookId"],
            "content": compressed_content,
            "page_no": entry["page_no"]
        }
        compressed_entries.append(compressed_entry)
    return compressed_entries


@app.route('/', methods=['GET'])
def index():
    return "Hello"


@app.route('/generate', methods=['POST'])
def generate_json():

    if 'pdf_file' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files['pdf_file']

    if pdf_file.filename == '':
        return jsonify({"error": "PDF file is empty"}), 400
    temp_dir = tempfile.TemporaryDirectory()
    temp_file_path = os.path.join(temp_dir.name, pdf_file.filename)

    pdf_file.save(temp_file_path)

    pdf_document = fitz.open(temp_file_path)
    image = request.files['profile']
    image_read = image.read()
    image_base64 = base64.b64encode(image_read).decode('utf-8')

    book_info = {
        "title": pdf_file.filename,
        "image": image_base64,
        "published": "Publication Year",
        "totalPage": len(pdf_document),
    }
    insertResponse = supabase.table('Book').insert(book_info).execute()

    data, count = supabase.table('Book').select('id').eq(
        'title', book_info["title"]).execute()

    contents = []

    print(pdf_document)
    # pageId = 122
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")

        content = {
            # "id": pageId,
            "bookId": data[1][0]['id'],
            "content": page_text,
            "page_no": page_number + 1,
        }
        # pageId = pageId + 1
        contents.append(content)
    compressed_content = compress_content_entries(contents)
    insertResponse = supabase.table('BookContent').insert(contents).execute()

    pdf_document.close()

    book_data = {"book": book_info, "contents": compressed_content}
    return jsonify(book_data)


if __name__ == '__main__':
    app.run()
