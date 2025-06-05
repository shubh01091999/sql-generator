import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

# Get API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("API key not found. Make sure it's defined in your .env file as GOOGLE_API_KEY.")
    st.stop()

# Configure Google Generative AI
genai.configure(api_key=API_KEY)

# Set up LLM
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash',
    google_api_key=API_KEY,
    temperature=0.4
)

# Streamlit UI
st.set_page_config(page_title="Entity/SQL Tool", layout="centered")
st.title("🛠️ Entity/SQL Script Tool")

# Initialize session state
if "operation" not in st.session_state:
    st.session_state.operation = "Entity to SQL"
if "entity_input" not in st.session_state:
    st.session_state.entity_input = ""
if "db_choice" not in st.session_state:
    st.session_state.db_choice = "MySQL"

# Handle operation change to clear input
def on_operation_change():
    st.session_state.entity_input = ""

# Operation selection
with st.sidebar:
    st.header("Configuration")
    operation = st.selectbox(
      "Choose Your Operation",
      ["Entity to SQL", "SQL to Entity", "Explain SQL"],
      key="operation",
      on_change=on_operation_change
)
    db_choice = st.selectbox(
      "Select Target Database",
      ["MySQL", "PostgreSQL", "Oracle", "SQL Server"],
      key="db_choice"
)

uploaded_file = st.file_uploader("Upload a .java or .sql file", type=['java', 'sql'])
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    st.session_state.entity_input = content

# Text area input (bound to session state)
entity_input = st.text_area("Paste your content here", height=300, key="entity_input")

# Prompt templates
prompt_map = {
    "Entity to SQL": """
You are a SQL migration assistant.
Target database: {db}

Given this Java Spring Boot Entity class:
{entity}

Generate:
1. Forward SQL to create this table.
2. Rollback SQL to drop this table.

Use syntax specific to {db}. Return only SQL code.
""",
    "SQL to Entity": """
You are a Java Spring Boot assistant.
Target database: {db}

Given this SQL table definition:
{entity}

Generate a Java Spring Boot JPA Entity class for the table.
Use proper annotations like @Entity, @Id, @Column, etc.
Return Java code only. No explanation.
""",
    "Explain SQL": """
You are a technical writer.

Given this SQL script:
{entity}

Explain what the SQL does in simple, clear English.
Only return explanation — no code or comments.
"""
}

# Build chain
prompt = PromptTemplate(
    template=prompt_map[st.session_state.operation],
    input_variables=["entity", "db"] if st.session_state.operation != "Explain SQL" else ["entity"]
)
chain = prompt | llm

# Generate button
if st.button("Generate"):
    if st.session_state.entity_input.strip():
        with st.spinner("Generating..."):
            try:
                input_data = {"entity": st.session_state.entity_input.strip()}
                if st.session_state.operation != "Explain SQL":
                    input_data["db"] = st.session_state.db_choice

                result = chain.invoke(input_data)
                output = result.content if hasattr(result, 'content') else str(result)

                # Clean Markdown/code wrapping
                if output.startswith("```"):
                    output = output.strip("`").split("\n", 1)[-1].strip()

                st.markdown("### ✅ Generated Output")
                st.code(output, language="sql" if "SQL" in st.session_state.operation else "java")
                 # Show download button
                ext = "sql" if "SQL" in st.session_state.operation else "java"
                st.download_button(
                label="Download Output",
                data=output,
                file_name=f"output.{ext}",
                mime="text/plain"
                )
            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ Please paste content to generate output.")
