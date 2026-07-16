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
from graph_service import GraphService
from config import Config

app = Flask(__name__)

# Enable CORS for Angular frontend running on port 4205 (and 4200 just in case)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:4205", "http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Graph Service
graph_service = GraphService()

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/graph/upload', methods=['POST'])
def upload_document():
    """Upload PDF/TXT, run NER and Relationship Extraction, and index in Knowledge Graph"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF and TXT files are allowed"}), 400
            
        reliability = float(request.form.get("reliability", 1.0))
        filename = secure_filename(file.filename)
        file_content = file.read()
        
        result = graph_service.upload_document(file_content, filename, reliability)
        if result["success"]:
            return jsonify(result), 200
        return jsonify(result), 400
        
    except Exception as e:
        print(f"Error in upload_document: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/graph/query', methods=['POST'])
def query_graph():
    """Answer question with multi-hop reasoning path traced through knowledge graph"""
    try:
        data = request.json or {}
        query = data.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400
            
        result = graph_service.query_graph_qa(query)
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in query_graph: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/graph/data', methods=['GET'])
def get_graph_data():
    """Get all nodes and links in the current graph"""
    try:
        graph_data = graph_service.get_full_graph_data()
        return jsonify({
            "success": True,
            "graph": graph_data
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/graph/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents and metadata"""
    try:
        return jsonify({
            "success": True,
            "documents": graph_service.documents
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/graph/clear', methods=['DELETE'])
def clear_graph():
    """Clear knowledge graph"""
    try:
        success = graph_service.clear_graph()
        return jsonify({
            "success": success,
            "message": "Knowledge Graph cleared successfully" if success else "Failed to clear graph"
        }), 200 if success else 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Flask server on port {Config.FLASK_PORT}...", flush=True)
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
