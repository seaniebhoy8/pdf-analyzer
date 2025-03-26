import requests
import json
import os
import argparse
from typing import Dict, Any
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
import tempfile

# Load environment variables from .env file
load_dotenv()

class LandingAIDocumentExtractor:
    def __init__(self, api_key: str):
        """
        Initialize the LandingAI Document Extractor.
        
        Args:
            api_key (str): Your LandingAI API key
        """
        self.api_key = api_key
        self.base_url = "https://api.va.landing.ai/v1/tools/agentic-document-analysis"
        self.headers = {
            "Authorization": f"Basic {api_key}",
            "Accept": "application/json"
        }

    def extract_pages_from_pdf(self, input_path: str, start_page: int, end_page: int) -> str:
        """
        Extract specific pages from a PDF and save to a temporary file.
        
        Args:
            input_path (str): Path to the input PDF
            start_page (int): Start page number (1-indexed)
            end_page (int): End page number (1-indexed)
            
        Returns:
            str: Path to the temporary file containing extracted pages
        """
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()

        # Read the PDF
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Convert to 0-based indexing
        start_idx = start_page - 1
        end_idx = end_page - 1

        # Validate page numbers
        if start_idx < 0 or end_idx >= len(reader.pages):
            raise ValueError(f"Invalid page numbers. PDF has {len(reader.pages)} pages.")

        # Add selected pages to the new PDF
        for page_num in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[page_num])

        # Save the new PDF
        with open(temp_path, 'wb') as output_file:
            writer.write(output_file)

        return temp_path

    def process_markdown_content(self, markdown_content: str) -> Dict[str, Any]:
        """
        Process the markdown content to extract sections, subsections, and assets.
        
        Args:
            markdown_content (str): The markdown content from the API response
            
        Returns:
            Dict[str, Any]: Structured content with sections and assets
        """
        # Split content into lines
        lines = markdown_content.split('\n')
        
        sections = []
        current_section = None
        current_subsection = None
        raw_content = []
        
        for line in lines:
            # Store raw content
            raw_content.append(line)
            
            # Check for section headers (h1)
            if line.startswith('# '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line[2:].strip(),
                    'subsections': [],
                    'assets': []
                }
            # Check for subsection headers (h2)
            elif line.startswith('## '):
                if current_section:
                    if current_subsection:
                        current_section['subsections'].append(current_subsection)
                    current_subsection = {
                        'title': line[3:].strip(),
                        'original_text': '',
                        'analyzed_text': ''
                    }
            # Check for asset information
            elif line.startswith('**Asset Type:**'):
                if current_section:
                    asset_type = line.replace('**Asset Type:**', '').strip()
                    current_section['assets'].append({
                        'type': asset_type,
                        'description': '',
                        'tag': ''
                    })
            # Check for asset description
            elif line.startswith('**Description:**'):
                if current_section and current_section['assets']:
                    current_section['assets'][-1]['description'] = line.replace('**Description:**', '').strip()
            # Check for asset tag
            elif line.startswith('**Tag:**'):
                if current_section and current_section['assets']:
                    current_section['assets'][-1]['tag'] = line.replace('**Tag:**', '').strip()
            # Regular content
            elif line.strip():
                if current_subsection:
                    if line.startswith('Original:'):
                        current_subsection['original_text'] = line.replace('Original:', '').strip()
                    elif line.startswith('Analyzed:'):
                        current_subsection['analyzed_text'] = line.replace('Analyzed:', '').strip()
                    else:
                        current_subsection['analyzed_text'] += '\n' + line.strip()
        
        # Add the last section if exists
        if current_section:
            if current_subsection:
                current_section['subsections'].append(current_subsection)
            sections.append(current_section)
        
        return {
            'sections': sections,
            'raw_content': raw_content
        }

    def extract_document(self, file_path: str, file_type: str = "image", start_page: int = None, end_page: int = None) -> Dict[str, Any]:
        """
        Extract structured information from a document.
        
        Args:
            file_path (str): Path to the document file
            file_type (str): Type of file - either "image" or "pdf"
            start_page (int, optional): Start page number for PDF extraction
            end_page (int, optional): End page number for PDF extraction
            
        Returns:
            Dict[str, Any]: Extracted structured information
        """
        try:
            # If PDF and page range specified, extract those pages first
            if file_type == "pdf" and start_page is not None and end_page is not None:
                print(f"Extracting pages {start_page} to {end_page} from PDF...")
                file_path = self.extract_pages_from_pdf(file_path, start_page, end_page)
                print(f"Created temporary PDF with selected pages: {file_path}")

            # Read the file in binary mode
            with open(file_path, 'rb') as file:
                # Determine the correct file parameter based on file type
                file_param = "image" if file_type.lower() == "image" else "pdf"
                files = {file_param: (os.path.basename(file_path), file, 'application/pdf' if file_type == 'pdf' else 'image/jpeg')}
                
                print(f"Sending request to {self.base_url}")
                print(f"Using file parameter: {file_param}")
                print(f"File name: {os.path.basename(file_path)}")
                
                # Make the API request
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    files=files
                )
                
                # Print response details for debugging
                print(f"Response status code: {response.status_code}")
                print(f"Response headers: {response.headers}")
                if response.status_code != 200:
                    print(f"Response content: {response.text}")
                
                # Check if the request was successful
                response.raise_for_status()
                
                # Get the response data
                response_data = response.json()
                
                # Process the markdown content to extract structured data
                markdown_content = response_data.get('data', {}).get('markdown', '')
                structured_data = self.process_markdown_content(markdown_content)
                
                # Add the structured data to the response
                response_data['data'].update(structured_data)
                
                return response_data
                
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            if hasattr(e.response, 'text'):
                print(f"Error details: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error processing document: {e}")
            raise
        finally:
            # Clean up temporary file if it was created
            if file_type == "pdf" and start_page is not None and end_page is not None:
                try:
                    os.unlink(file_path)
                except:
                    pass

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extract information from documents using LandingAI API')
    parser.add_argument('document_path', help='Path to the document file (PDF or image)')
    parser.add_argument('--file-type', choices=['pdf', 'image'], default='pdf',
                      help='Type of file (pdf or image). Default is pdf')
    parser.add_argument('--start-page', type=int, help='Start page number for PDF extraction')
    parser.add_argument('--end-page', type=int, help='End page number for PDF extraction')
    
    args = parser.parse_args()

    # Get API key from environment variable
    api_key = os.getenv("LANDING_AI_API_KEY")
    if not api_key:
        raise ValueError("Please set the LANDING_AI_API_KEY environment variable in your .env file")

    # Initialize the extractor
    extractor = LandingAIDocumentExtractor(api_key)
    
    try:
        # Extract information from the document
        result = extractor.extract_document(
            args.document_path, 
            args.file_type,
            start_page=args.start_page,
            end_page=args.end_page
        )
        
        # Print the extracted information
        print("Extracted Document Information:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Failed to extract document: {e}")

if __name__ == "__main__":
    main()
