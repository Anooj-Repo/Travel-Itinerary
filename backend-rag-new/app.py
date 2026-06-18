import os
import requests
import urllib3

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkeypatch requests to disable SSL verification globally
original_request = requests.Session.request
requests.Session.request = lambda self, method, url, **kwargs: original_request(self, method, url, **dict(kwargs, verify=False))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from rag_service import RAGService
from config import Config

app = Flask(__name__)

# Enable CORS for Angular frontend running on port 4202 (and 4200 just in case)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4202", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize RAG service
rag_service = RAGService()

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/impact/upload', methods=['POST'])
def upload_document():
    """Upload business spec (PDF/TXT) and index into FAISS"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF and TXT files are allowed"}), 400
            
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        result = rag_service.upload_document(file_content, filename)
        if result["success"]:
            return jsonify(result), 200
        return jsonify(result), 400
        
    except Exception as e:
        print(f"Error in upload_document: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/impact/summarize', methods=['POST'])
def generate_summary():
    """Generate impact analysis report from FAISS index"""
    try:
        report = rag_service.generate_impact_summary()
        return jsonify({
            "success": True,
            "report": report
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/impact/chat', methods=['POST'])
def chat():
    """Chat with system. Supports text, image attachment (base64)"""
    try:
        data = request.json or {}
        query = data.get("query", "")
        image_base64 = data.get("image", None) or data.get("image_base64", None)
        
        response = rag_service.chat_with_docs(query, image_base64)
        return jsonify({
            "success": True,
            "response": response
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/impact/documents', methods=['GET'])
def get_documents():
    """List uploaded files"""
    try:
        docs_info = rag_service.get_documents()
        return jsonify({
            "success": True,
            "documents": docs_info
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/impact/documents/clear', methods=['DELETE'])
def clear_documents():
    """Clear FAISS vector store"""
    try:
        success = rag_service.clear_documents()
        return jsonify({
            "success": success,
            "message": "All documents cleared successfully" if success else "Failed to clear documents"
        }), 200 if success else 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
