# 🏥 Insurance Claims Processing Agent

An AI-powered insurance claims processing system using **LangGraph**, **RAG**, and **GPT-4o-mini** to automate claim validation, policy retrieval, and decision-making.

## 🚀 Features

- ✅ **Automated Claims Processing**: Parse, validate, and adjudicate insurance claims
- 🔍 **RAG-based Policy Retrieval**: Intelligent retrieval from policy documents using ChromaDB
- 🤖 **LangGraph Workflow**: Structured multi-step agent workflow
- 📊 **Interactive UI**: Streamlit interface for manual entry or JSON upload
- 📝 **Detailed Logging**: Complete audit trail of all agent decisions
- 🐳 **Docker Support**: Easy deployment with Docker

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional, for containerized deployment)

## 🛠️ 3 Methods of Installation

### 1. Deploy on AWS EC2 Instance (Clone GitHub  →  Build Docker Image  →  Docker Run)
### Refer : [AWS_EC2_Deployment_Steps.md](AWS_EC2_Deployment_Steps.md)

<br>

### 2. Use Pre-Built Docker Image from Docker Hub (Docker Image Pull  →  Docker Run)
### Refer : [Docker_HUB_TO_Instance.md](Docker_HUB_TO_Instance.md)

<br>

### 3. Local Setup in your instance

<br>

1. **Clone the repository**
    ```bash
    git clone https://github.com/Gr8Learning-2312/insurance-agent.git
    cd insurance-agent
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv virtual_environment
    
    # Windows
    virtual_environment\Scripts\activate
    
    # Linux/Mac
    source virtual_environment/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    *   Find the `.env` file in the project root.
    *   Add your OpenAI API Key & OpenAI Base URL:
        ```env
        OPENAI_API_KEY="gl-xxxxxxxxxx"      #  Add your OpenAI API Key
        OPENAI_BASE_URL="https....../v1"    #  Add your OpenAI Base URL
        ```

## Running the Application

1.  **Start the Streamlit server**:
    ```bash
    streamlit run app/main.py
    ```

2.  **Access the Web Interface**:
    *   Open your web browser and go to: `http://localhost:8501`



## Usage

1.  Enter your insurance claim details manually or upload the claim details in the JSON format
2.  Click **"Process Claim"**, to check if the claim is to be Approved or Rejected.
3.  Monitor the **Logs** of the agent.
