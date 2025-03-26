# PDF Document Analyzer

A web application that uses LandingAI's API to analyze PDF documents and extract structured information.

## Features
- Upload and analyze PDF documents
- Extract specific pages for analysis
- Beautiful web interface with color-coded results
- Real-time analysis with LandingAI

## Local Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your LandingAI API key:
   ```
   LANDING_AI_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   python -m flask run
   ```

## Deployment on Render

1. Create a Render account at https://render.com
2. Create a new Web Service
3. Connect your GitHub repository
4. Set the following environment variables in Render:
   - `LANDING_AI_API_KEY`: Your LandingAI API key
5. Deploy!

## Usage

1. Open the web interface
2. Enter the start and end page numbers you want to analyze
3. Click "Analyze Pages"
4. View the color-coded results:
   - Original text in gray
   - Analyzed content in green
   - Sections and subsections clearly marked

## Security Note

Never commit your `.env` file or expose your API key. Always use environment variables for sensitive information. 