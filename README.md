# CV Analysis System

An intelligent Hiring Assistant powered by RAG (Retrieval Augmented Generation) and LangChain. This system allows HR professionals to upload CVs, automatically extract and summarize insights, and interact with an AI agent to evaluate and compare candidates.

## 🚀 Features

- **CV Ingestion & Processing**: Upload PDF CVs which are automatically processed, summarized, and indexed for search.
- **Intelligent HR Agent**: A conversational AI that acts as an expert HR assistant.
- **Candidate Comparison**: Ask the agent to compare multiple candidates based on specific criteria (e.g., "Who has the most experience with Django?").
- **Deep Dive Analysis**: Query specific details about a candidate's experience, education, or skills.
- **RAG-Powered**: Uses Vector Search (ChromaDB) to retrieve accurate information from candidate documents, ensuring the AI answers based on facts, not hallucinations.

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Framework**: Django
- **AI/LLM**: LangChain, OpenAI GPT
- **Vector Store**: ChromaDB
- **Dependency Management**: Poetry

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cv-analysis-system
   ```

2. **Install Dependencies**
   This project uses [Poetry](https://python-poetry.org/) for dependency management.
   ```bash
   poetry install
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory (or copy from example if available) and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   # Add other necessary variables if any
   ```

4. **Database Migration**
   Initialize the SQLite database and vector store settings.
   ```bash
   poetry run python manage.py migrate
   ```

## 🏃‍♂️ Usage

1. **Start the Development Server**
   ```bash
   poetry run python manage.py runserver
   ```

2. **Access the Application**
   Open your browser and navigate to `http://localhost:8000`.

3. **Workflow**
   - **Upload**: Go to the documents section to upload candidate CVs.
   - **Process**: The system will ingest and index the documents.
   - **Chat**: Navigate to the Chatbot interface.
   - **Interact**:
     - *Comparative*: "Compare the candidates based on their Python experience."
     - *Specific*: "Does Candidate X have any leadership experience?"
     - *Discovery*: "Find me a candidate with strong background in Finance."

## 🤖 Agent Capabilities

The agent is equipped with specialized tools:
- `search_cv_summaries`: For high-level comparisons and ranking.
- `search_cv_details`: For extracting specific evidence from a candidate's full CV.
- `list_all_cvs`: To see who is currently in the system.

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
