import streamlit as st
import sys
import os

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.rag_chain import answer_question

from backend.speech_to_text import transcribe_audio

st.set_page_config(page_title="Value Investing AI", layout="wide")

st.title("Value Investing RAG Chatbot")
st.write("Ask questions about the value investing videos via Text or Audio.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Audio Input
audio_value = st.audio_input("Record a question")
prompt = None

if audio_value:
    with st.spinner("Transcribing audio..."):
        text = transcribe_audio(audio_value)
        if text:
            st.info(f"Transcribed: {text}")
            prompt = text

# Text Input (fallback or primary)
if not prompt:
    prompt = st.chat_input("What is your question?")

if prompt:
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = answer_question(prompt)
                st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")
