# CV Analysis System

This is a Django-based system for analyzing CVs, extracting relevant information, and enabling chatbot-based querying.

## Features
- Upload and parse CVs
- Store extracted information in a database
- Query CV data using a chatbot interface

## Setup Instructions

### Prerequisites
- Python 3.8+ installed
- `pip` installed

### Installation

1. **Clone the repository**:
   - git clone https://github.com/OssOss13/cv-analysis-system.git
   - cd cv-analysis-system


2. **Set up a virtual environment**
   - python -m venv venv
   - source venv/bin/activate  
   - On Windows use: venv\Scripts\activate

3. **Install Tesseract OCR**
   - Install from https://github.com/UB-Mannheim/tesseract/wiki
   - Add it to your system PATH like: C:\Program Files\Tesseract-OCR

5. **Install dependencies**
   - pip install -r requirements.txt

6. **Set up environment variables**
   - Copy .env.example to .env and update values.

7. **Run database migrations**
   - python manage.py migrate

8. **Create a superuser (optional, for admin access)**
   - python manage.py createsuperuser

9. **python manage.py runserver**
   - python manage.py runserver

10. **Access the application**
    - Open http://127.0.0.1:8000/ in your browser.
