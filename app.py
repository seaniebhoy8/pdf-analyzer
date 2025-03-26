from flask import Flask, render_template, request, jsonify
import os
from main import LandingAIDocumentExtractor
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the document extractor
api_key = os.getenv("LANDING_AI_API_KEY")
if not api_key:
    raise ValueError("Please set the LANDING_AI_API_KEY environment variable in your .env file")
extractor = LandingAIDocumentExtractor(api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get the page numbers from the form
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 2))
        
        print(f"Received request to analyze pages {start_page} to {end_page}")
        
        # Validate page numbers
        if end_page - start_page + 1 > 2:
            return jsonify({
                'error': 'Maximum 2 pages can be analyzed at once'
            }), 400
        
        # Check if file exists
        pdf_path = "WATERPRO-Petrol-Engine-Driven-Pump-Instruction-Manual.pdf"
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at {pdf_path}")
            return jsonify({
                'error': 'PDF file not found'
            }), 404
        
        print(f"Starting document analysis...")
        # Analyze the document
        result = extractor.extract_document(
            pdf_path,
            file_type="pdf",
            start_page=start_page,
            end_page=end_page
        )
        
        print("Document analysis completed successfully")
        
        # Extract the markdown content and metadata
        markdown_content = result.get('data', {}).get('markdown', '')
        structured_data = result.get('data', {}).get('sections', [])
        raw_content = result.get('data', {}).get('raw_content', [])
        
        # Create metadata structure
        metadata = {
            'file_name': os.path.basename(pdf_path),
            'file_type': 'PDF',
            'folder_path': os.path.dirname(os.path.abspath(pdf_path)),
            'page_range': f"{start_page}-{end_page}",
            'total_pages': end_page - start_page + 1,
            'analysis_timestamp': result.get('timestamp', ''),
            'sections': structured_data,
            'assets': result.get('data', {}).get('assets', [])
        }
        
        return jsonify({
            'success': True,
            'content': markdown_content,
            'raw_content': raw_content,
            'metadata': metadata
        })
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Run the app with default settings
    app.run(debug=True) 