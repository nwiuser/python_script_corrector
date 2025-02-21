import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
import json

# Set page config - MUST be the first Streamlit command
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

# Initialize Gemini API
def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Please set GEMINI_API_KEY environment variable")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'model' not in st.session_state:
    st.session_state.model = init_gemini()
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")

def save_chat():
    """Save current chat to history"""
    if st.session_state.messages:
        chat_data = {
            'id': st.session_state.current_chat_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'title': st.session_state.messages[0]['content'][:50] + "..." if st.session_state.messages else "Empty Chat",
            'messages': st.session_state.messages
        }
        
        # Update existing chat or add new one
        existing_chat_idx = next((i for i, chat in enumerate(st.session_state.chat_history) 
                                if chat['id'] == st.session_state.current_chat_id), None)
        if existing_chat_idx is not None:
            st.session_state.chat_history[existing_chat_idx] = chat_data
        else:
            st.session_state.chat_history.append(chat_data)

def load_chat(chat_id):
    """Load a chat from history"""
    chat = next((chat for chat in st.session_state.chat_history if chat['id'] == chat_id), None)
    if chat:
        st.session_state.messages = chat['messages']
        st.session_state.current_chat_id = chat_id

def export_chat_history():
    """Export chat history as JSON"""
    if st.session_state.chat_history:
        return json.dumps({
            'chats': st.session_state.chat_history
        }, indent=2)
    return None

# Sidebar
with st.sidebar:
    st.title("Settings")
    temperature = 0.35
    
    # Chat History Section
    st.markdown("---")
    st.subheader("💬 Chat History")
    
    # New Chat button
    if st.button("New Chat"):
        save_chat()  # Save current chat before creating new one
        st.session_state.messages = []
        st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.rerun()
    
    # Display chat history
    st.markdown("#### Previous Chats")
    for chat in reversed(st.session_state.chat_history):
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📝 {chat['title']}", key=f"chat_{chat['id']}"):
                save_chat()  # Save current chat before loading
                load_chat(chat['id'])
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat['id']}"):
                st.session_state.chat_history.remove(chat)
                if chat['id'] == st.session_state.current_chat_id:
                    st.session_state.messages = []
                    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.rerun()
    
    # Export functionality
    st.markdown("---")
    if st.button("Export Chat History"):
        export_data = export_chat_history()
        if export_data:
            st.download_button(
                label="Download JSON",
                data=export_data,
                file_name="chat_history.json",
                mime="application/json"
            )
    
    if st.button("Clear All History"):
        if st.session_state.chat_history:
            st.session_state.chat_history = []
            st.session_state.messages = []
            st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

# Main content area
st.title("AI Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(f"{message['content']}")
        if message["role"] == "assistant":
            st.caption(f"Generated at {message['timestamp']}")

# Chat input
if prompt := st.chat_input("Enter your message..."):
    
    gemini_prompt = """ Correct the following Python script for errors.  Focus *only* on fixing errors that prevent the code from running correctly or producing the intended output. Do not suggest style changes or optimizations unless they are directly related to fixing a bug.
    """ + prompt
    # Add user message
    st.session_state.messages.append({"role": "user", "content": gemini_prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.model.generate_content(
                    gemini_prompt,
                    generation_config={
                        'temperature': temperature,
                        'top_p': 1,
                        'top_k': 1,
                        'max_output_tokens': 1000,
                    }
                )
                st.write(response.text)
                # timestamp = datetime.now().strftime("%H:%M:%S")
                # st.caption(f"Generated at {timestamp}")
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.text,
                    # "timestamp": timestamp
                })
                
                # Save chat to history
                save_chat()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.caption("Made with Streamlit and Google's Gemini AI")