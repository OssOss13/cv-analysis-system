import fitz, docx, json
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io, os, re
from .models import CV, WorkExperience, Education, Project, Certification, Skill, PersonalInfo
from django.db import transaction
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

client = OpenAI(
    organization=os.getenv("OPENAI_ORG"),
    project=os.getenv("OPENAI_PROJECT"),
    api_key=os.getenv("OPENAI_API_KEY")  
)

# Function to parse CV text
def parse_cv(cv_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts personal info, work experience, projects, certifications, and skills from a CV text."},
            {"role": "user", "content": f"""Extract the following details from this CV text: personal info (name, email, phone, linkedin, github), work experience, projects, certifications, and skills. Return the data in a JSON format. Like: return {{
                "personal_info": personal_info,
                "education": education,
                "work_experience": work_experience,
                "projects": projects,
                "certifications": certifications,
                "skills": skills
            }}. The response should be concise; don't add anything except for the requested JSON. The Certification fields names should be title, issuer, description, year (if any). The work experience fields names should be title, company, years, location (if any). The education fields names should be degree, institution, years, location (if any). Projects should be title and description (if any). CV text: {cv_text}"""},
        ],
        stream=False
    )

    # Extract the parsed data from the response
    parsed_data = response.choices[0].message.content
    print(parsed_data)
    return parsed_data


def preprocess_image(image):
    """Preprocess image to improve OCR accuracy."""
    image = image.convert("L")  # Convert to grayscale
    image = image.filter(ImageFilter.MedianFilter())  # Reduce noise
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Increase contrast
    return image

def extract_text_from_cv(file_path):
    """Extract text from a scanned CV (PDF) using OCR with proper preprocessing."""
    text = ""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        print("Processing PDF...")
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                print(f"Processing page {page_num + 1}...")

                # Convert page to image (300 DPI for better OCR)
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))

                # Preprocess image before OCR
                img = preprocess_image(img)

                # OCR extraction with better page segmentation mode
                page_text = pytesseract.image_to_string(img, config="--psm 3")  
                text += page_text + "\n"

    elif ext == ".docx":
        print("Processing DOCX...")
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    print("Extracted Text:", text)
    return text.strip()

def clean_linkedin_url(linkedin):
    """Ensures LinkedIn URL is valid and not mistakenly removed."""
    if linkedin and linkedin.strip().lower() == "www.":  
        return None  # Discard "www." only if it is exactly that
    return linkedin  # Otherwise, keep the original valid link


def clean_phone_number(phone):
    """Removes special characters like () and - from phone numbers."""
    return re.sub(r"[^\d+]", "", phone) if phone else None


def extract_name(text):
    """Extracts name from the top of the CV using regex, then validates with NLP."""
    lines = text.split("\n")[:10]  # Check only the top 10 lines (most likely to have the name)
    
    # Basic regex pattern for detecting full names (First Last format)
    name_pattern = r"^[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?$" 
    for line in lines:
        line = line.strip()
        if re.match(name_pattern, line):
            return line  # If regex finds a name, return it immediately

    # Use NLP only if regex fails
    doc = nlp(text)
    tech_keywords = {"java", "oracle", "python", "c++", "sql", "react", "aws", "django"}  # Words to exclude
    for ent in doc.ents:
        if ent.label_ == "PERSON" and ent.text.lower() not in tech_keywords:
            return ent.text  # Return first detected proper name

    return None  # Return None if no valid name is found

def extract_personal_info(text):
    """Extracts name, email, phone, and social links from CV text."""
    
    # Extract email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email = re.findall(email_pattern, text)
    
    # Extract phone number
    phone_pattern = r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    phone = re.findall(phone_pattern, text)

    # Extract LinkedIn and GitHub URLs
    linkedin_pattern = r"https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+"
    github_pattern = r"https?://(www\.)?github\.com/[a-zA-Z0-9_-]+"
    
    linkedin = re.findall(linkedin_pattern, text)
    github = re.findall(github_pattern, text)


    name = extract_name(text)

    return {
        "name": name if name else None,
        "email": email[0] if email else None,
        "phone": clean_phone_number(phone[0]) if phone else None,
        "linkedin": clean_linkedin_url(linkedin[0]) if linkedin else None,
        "github": github[0] if github else None
    } 


def classify_text(lines):
    """Classifies CV text as Education, Work Experience, Projects, or Certifications based on keywords."""
    education = []
    work_experience = []
    projects = []
    certifications = []

    education_keywords = ["university", "bachelor", "master", "phd", "college", "degree", "institute", "GPA"]
    work_experience_keywords = ["experience", "worked", "intern", "developer", "engineer", "company", "position", "role"]
    project_keywords = ["built", "developed", "created", "designed", "implemented", "open-source", "GitHub"]
    certification_keywords = ["certified", "certification", "course", "training", "license"]

    for line in lines:
        lower_line = line.lower()

        if any(word in lower_line for word in education_keywords):
            education.append(line)
        elif any(word in lower_line for word in work_experience_keywords):
            work_experience.append(line)
        elif any(word in lower_line for word in project_keywords):
            projects.append(line)
        elif any(word in lower_line for word in certification_keywords):
            certifications.append(line)

    return {
        "education": "\n".join(education),
        "work_experience": "\n".join(work_experience),
        "projects": "\n".join(projects),
        "certifications": "\n".join(certifications)
    }
    

def extract_skills(text):
    """Extracts technical skills from CV text."""
    skills_list = [
        "Python", "Django", "React", "JavaScript", "SQL",
        "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning",
        "NLP", "Data Science", "Flask", "FastAPI", "REST API",
        "Git", "Docker", "Kubernetes", "CI/CD", "AWS", "Azure"
    ]

    found_skills = [skill for skill in skills_list if skill.lower() in text.lower()]

    return {"skills": found_skills}


# def parse_cv(text):
#     """Parses a CV and extracts structured information."""
    
#     personal_info = extract_personal_info(text)  
#     # sections = extract_sections(text)  

#     # If sections are empty, classify based on keywords
#     classified_data = classify_text(text.split("\n")) 

#     return {
#         "personal_info": personal_info,
#         "education": classified_data.get("education", ""),
#         "work_experience": classified_data.get("work_experience", ""),
#         "projects": classified_data.get("projects", ""),
#         "certifications": classified_data.get("certifications", ""),
#         "skills": extract_skills(text)["skills"]
#     }

def save_cv_to_db(cv, parsed_data):
    """Saves parsed CV data to the database."""
    
    # Ensure parsed_data is not empty before attempting JSON parsing
    if not parsed_data:
        print("Parsed data is empty or invalid.")
        return cv  
    
    # If parsed_data is a string, check for triple backticks and remove them
    if isinstance(parsed_data, str):
        # Use regex to remove ```json and ``` from the string
        parsed_data = re.sub(r'```json|```', '', parsed_data).strip()


    try:
        if isinstance(parsed_data, str):  # Ensure it's a dictionary, not a string
            parsed_data = json.loads(parsed_data)  # Convert JSON string to dictionary
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return cv  # Return early if parsing fails

    if not parsed_data:  # Check if JSON is empty
        print("Parsed data is empty after parsing.")
        return cv  

    # Using transaction to prevent partial saves
    with transaction.atomic():
        # Save personal information
        personal_info = parsed_data.get("personal_info", {})

        PersonalInfo.objects.create(
            cv=cv,
            name=(personal_info.get("name") or "").strip(),
            email=(personal_info.get("email") or "").strip(),
            phone=personal_info.get("phone"),  # Allow NULL values
            linkedin=(personal_info.get("linkedin") or "").strip() if personal_info.get("linkedin") else None,
            github=(personal_info.get("github") or "").strip() if personal_info.get("github") else None,
        )

        # Save work experience
        for exp in parsed_data.get("work_experience", []):  
            print("expppp:  ", exp)
            if isinstance(exp, dict):  
                job_title = (exp.get("title") or "").strip()
                company = (exp.get("company") or "").strip()
                years = (exp.get("years") or "").strip()  
                location = (exp.get("location") or "").strip()

                if job_title:  
                    WorkExperience.objects.create(
                        cv=cv,
                        job_title=job_title,
                        company=company,
                        duration=years,
                        location=location,
                    )

        # Save education
        for edu in parsed_data.get("education", []):  
            if isinstance(edu, dict):  
                degree = (edu.get("degree") or "").strip()
                institution = (edu.get("institution") or "").strip()
                duration = (edu.get("years") or "").strip()
                location = (edu.get("location") or "").strip()

                if degree:  
                    Education.objects.create(
                        cv=cv,
                        degree=degree,
                        institution=institution,
                        duration=duration,
                        location=location,
                    )

        # Save projects (if available)
        for proj in parsed_data.get("projects", []):  
            if isinstance(proj, dict):  
                title = (proj.get("title") or "").strip()
                description = (proj.get("description") or "").strip()

                if title:  
                    Project.objects.create(
                        cv=cv,
                        title=title,
                        description=description,
                    )

        # Save certifications
        for cert in parsed_data.get("certifications", []):  
            if isinstance(cert, dict):  
                name = (cert.get("title") or "").strip()
                issuer = (cert.get("issuer") or "").strip()
                description = (cert.get("description") or "").strip()
                year = (cert.get("year") or "").strip()

                if name:  
                    Certification.objects.create(
                        cv=cv,
                        name=name,
                        issuer=issuer,
                        description=description,
                        year=year,  
                    )

        # Save skills
        for skill in parsed_data.get("skills", []):  
            if isinstance(skill, str):  # If skill is a string
                skill_name = skill.strip()
                if skill_name:  
                    Skill.objects.create(cv=cv, name=skill_name)

    return cv