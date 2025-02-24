from django.apps import apps
from openai import OpenAI
from documents.models import CV, WorkExperience, Education, Project, Skill, Certification, PersonalInfo
import re, os
from dotenv import load_dotenv
from django.db.models import Q

load_dotenv()
               
client = OpenAI(
    organization=os.getenv("OPENAI_ORG"),
    project=os.getenv("OPENAI_PROJECT"),
    api_key=os.getenv("OPENAI_API_KEY")  
)

def summarize_and_remove_dups(input_data):
    if not input_data:
        return "No data available to summarize."

    try:
        # Define the system prompt to guide the model
        system_prompt = """
        You are a smart assistant that processes candidate records. Your task is to:
        - Remove duplicate entries.
        - Summarize redundant information while preserving key details.
        - Return the data in the exact same format as the input.
        - Do not alter candidate names or remove unique experiences, education, or projects.
        """

        # Call OpenAI's GPT model for summarization
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": f"Process the following candidate data:\n{input_data}"}
            ],
            temperature=0.3  # Low temperature for factual summarization
        )
        
        response = response.choices[0].message.content
        print('summary response: ', response)

        print('len before : ', len(input_data))
        print('summary response len: ', len(response))
        return response  # Convert back to dictionary format

    except Exception as e:
        return f"Error summarizing data: {str(e)}"


    

def classify_query_with_gpt(user_query):
    prompt = f"""I will be retrieving data from a database. Analyze the following query and determine whether it asks for general information that will need all the records from the database, or a filtered search based on a keyword. 
    WorkExperience, Education, Project, Skill and Certification are the available tables.
    If it's general (will need all records from a table), respond with 'general:<table_name>'. If it requires filtering, respond with 'filter:<keyword>:<table_name>'
    Query: "{user_query}"
    
    Response:
    """
    response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "developer", "content": "You are a query analyzer for a CV database."},
                  {"role": "user", "content": prompt}],
                stream=False
            )
    response = response.choices[0].message.content
    # print('classified response:', len(response))
    return response


def get_all_records_by_candidate(table_name):
    try:
        # Dynamically get the model
        model = apps.get_model('documents', table_name)
        
        # Ensure the table has a 'cv' foreign key
        if not hasattr(model, 'cv'):
            return f"The table '{table_name}' does not reference a CV."

        # Fetch all records and group them by candidate name
        records = model.objects.select_related('cv__personal_info').all()
        print("records:", records)

        candidate_data = {}
        for record in records:
            candidate_name = record.cv.personal_info.name if record.cv and record.cv.personal_info else "Unknown Candidate"
            
            # Convert the record to a dictionary (excluding the CV reference)
            record_data = {field.name: getattr(record, field.name) for field in model._meta.fields if field.name not in ["id", "cv"]}
            
            if candidate_name not in candidate_data:
                candidate_data[candidate_name] = []
            
            candidate_data[candidate_name].append(record_data)

        # Format the result
        if candidate_data:
            result = "Candidate Data:\n" + "\n".join(
                f"{name}: {entries}" for name, entries in candidate_data.items()
            )
        else:
            result = f"No records found in the '{table_name}' table."

        print('all records result', result)
        return result

    except LookupError:
        return f"Table '{table_name}' not found."



def filter_data_from_db(table, keyword):
    relevant_data = ''
    keyword_lower = keyword.lower()
    
    if table.lower() == "skill":
        print('skill')
        skill_names = Skill.objects.values_list("name", flat=True).distinct()
        matched_skills = [skill for skill in skill_names if re.search(rf'\b{re.escape(skill)}\b', keyword_lower, re.IGNORECASE)]
        
        if not matched_skills:
            relevant_data = "No matching skills found."
        else:
            candidates = CV.objects.filter(skills__name__in=matched_skills).distinct().select_related('personal_info').prefetch_related('skills')
            
            if candidates.exists():
                relevant_data = "Candidates with matching skills:\n" + "\n".join(
                    f"{c.personal_info.name or 'Unknown Candidate'}: {', '.join(s.name for s in c.skills.all())}"
                    for c in candidates
                )
            else:
                relevant_data = "No candidates found with the specified skills."
    
    elif table.lower() == "education":
        print('education')
        user_keywords = re.findall(r'\b\w+\b', keyword_lower)
        queries = [Q(degree__icontains=kw) | Q(institution__icontains=kw) for kw in user_keywords]
        
        education_queryset = Education.objects.all()
        if queries:
            query = queries.pop()
            for q in queries:
                query |= q
            education_queryset = education_queryset.filter(query)
        
        candidate_ids = education_queryset.values_list('cv_id', flat=True).distinct()
        candidates = CV.objects.filter(id__in=candidate_ids).select_related('personal_info').prefetch_related('education')
        
        if candidates.exists():
            relevant_data = "Candidate education:\n" + "\n".join(
                f"{c.personal_info.name or 'Unknown Candidate'}: " + 
                ", ".join(f"{edu.degree} from {edu.institution}" for edu in c.education.all())
                for c in candidates
            )
        else:
            relevant_data = "No candidates found with matching education details."
    
    elif table.lower() == "experience":
        print("experience")
        user_keywords = re.findall(r'\b\w+\b', keyword_lower)
        queries = [Q(company__icontains=kw) | Q(job_title__icontains=kw) for kw in user_keywords]
        
        work_exp_queryset = WorkExperience.objects.all()
        if queries:
            query = queries.pop()
            for q in queries:
                query |= q
            work_exp_queryset = work_exp_queryset.filter(query)
        
        candidate_ids = work_exp_queryset.values_list('cv_id', flat=True).distinct()
        candidates = CV.objects.filter(id__in=candidate_ids).select_related('personal_info').prefetch_related('work_experience')
        
        if candidates.exists():
            relevant_data = "Candidate work experiences:\n" + "\n".join(
                f"{c.personal_info.name or 'Unknown Candidate'}: " + 
                ", ".join(f"{exp.company} ({exp.job_title})" for exp in c.work_experience.all())
                for c in candidates
            )
        else:
            relevant_data = "No candidates found with matching work experience."
    
    elif table.lower() == "project":
        print('projects')
        user_keywords = re.findall(r'\b\w+\b', keyword_lower)
        queries = [Q(title__icontains=kw) | Q(description__icontains=kw) for kw in user_keywords]
        
        project_queryset = Project.objects.all()
        if queries:
            query = queries.pop()
            for q in queries:
                query |= q
            project_queryset = project_queryset.filter(query)
        
        candidate_ids = project_queryset.values_list('cv_id', flat=True).distinct()
        candidates = CV.objects.filter(id__in=candidate_ids).select_related('personal_info').prefetch_related('projects')
        
        if candidates.exists():
            relevant_data = "Candidate projects:\n" + "\n".join(
                f"{c.personal_info.name or 'Unknown Candidate'}: " + 
                ", ".join(f"{proj.title} - {proj.description}" for proj in c.projects.all())
                for c in candidates
            )
        else:
            relevant_data = "No candidates found with matching projects."
    
    elif table.lower() == "certification":
        print('certification')
        user_keywords = re.findall(r'\b\w+\b', keyword_lower)
        queries = [Q(name__icontains=kw) | Q(issuer__icontains=kw) | Q(description__icontains=kw) for kw in user_keywords]
        
        cert_queryset = Certification.objects.all()
        if queries:
            query = queries.pop()
            for q in queries:
                query |= q
            cert_queryset = cert_queryset.filter(query)
        
        candidate_ids = cert_queryset.values_list('cv_id', flat=True).distinct()
        candidates = CV.objects.filter(id__in=candidate_ids).select_related('personal_info').prefetch_related('certifications')
        
        if candidates.exists():
            relevant_data = "Candidate certifications:\n" + "\n".join(
                f"{c.personal_info.name or 'Unknown Candidate'}: " + 
                ", ".join(cert.name for cert in c.certifications.all())
                for c in candidates
            )
        else:
            relevant_data = "No candidates found with matching certifications."
    print('filtered result : ', relevant_data)
    return relevant_data


def add_context_to_final_message(summarized_data, formatted_history, user_message):
    SYSTEM_PROMPT = """
        You are a helpful assistant that helps users query a CV database. You can assist with:
        1. Finding candidates with specific skills.
        2. Comparing education levels.
        3. Searching for experience in specific industries.
        4. Identifying matching candidates for job requirements.

        When responding:
        - Provide a clear, natural response in plain text.
        - Avoid using JSON formatting in your response.
        - If a user asks for candidates with a skill, explain that you will find candidates with that skill.
        - If a user asks to compare education levels, explain how education levels will be compared.
        - If a user asks for experience in an industry, describe how you will retrieve relevant candidates.
        - If the question is unclear, ask the user for clarification instead of guessing.
        - Don't respond in an HTML format. respond in only text format.
        Your goal is to provide a natural, human-like response that guides the user and explains what data will be retrieved.
        """
    
    response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                        {"role": "developer", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": "Here are the last 5 messages in our conversation:"},
                        ]+
                        formatted_history
                        +[
                        {"role": "user", "content": f"Here is the relevant data retrieved from the database:\n\n{summarized_data}"},
                        {"role": "user", "content": user_message}      
                    ],
                stream=False
            )

    bot_response = response.choices[0].message.content
    return bot_response