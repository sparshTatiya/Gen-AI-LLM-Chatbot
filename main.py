import datetime
import os
import sqlite3

from typing import Any, List, Dict

import openai
import google.generativeai as genai
import streamlit as st

from dotenv import load_dotenv

from db_ops import (
    init_db,
    get_recent_conversations,
    store_conversation_summary,
    store_message,
    create_user,
    authenticate_user
)

load_dotenv()

# Configure the Gemini API
os.environ["GEMINI_API_KEY"] = os.getenv("mr_shukla_GEMINI_API_KEY")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configure the OpenAI API
os.environ["OPENAI_API_KEY"] = os.getenv("mr_shukla_OPENAI_API_KEY")
openai.api_key = os.environ["OPENAI_API_KEY"]


# Available AI models
AI_MODELS = {"gemini": "gemini-2.0-flash", "openai": "gpt-4o-mini"}


def summarize_conversation(
    conversation: List[Dict[str, Any]], model_choice: str
) -> str:
    if not conversation:
        return "No conversations found"

    # Format conversastions for the model
    conversation_texts = []
    for idx, conv in enumerate(conversation):
        conv_text = f"Conversation {idx + 1} ({conv['timestamp']}) \n"
        for msg in conv["messages"]:
            conv_text += f'{msg["role"].upper()}: {msg["content"]}\n'
        conversation_texts.append(conv_text)

    conversation_texts = "\n\n".join(conversation_texts)
    prompt = f"""
Please provide a concise summary of the following conversations:
{conversation_texts}
Focus on key topics discussed, questions asked, and information provided.
Highlight any recurring themes or important points.
"""

    if model_choice == "gemini":
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_text(prompt)
        return response.text
    elif model_choice == "openai":
        response = openai.chat.completions.create(
            model="gpt-4-o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )

        return response.choices[0].message["content"]
    else:
        raise ValueError(f"Unsupported model choice: {model_choice}")


def chat_with_ai(
    prompt: str, chat_history: List[Dict[str, str]], model_choice: str
) -> str:
    try:
        if model_choice == "gemini":
            return chat_with_gemini(prompt, chat_history)
        elif model_choice == "openai":
            return chat_with_openai(prompt, chat_history)
        else:
            return "Invalid model selection. Please choose 'gemini' or 'openai'."

    except Exception as e:
        return f"Error occured with AI api: {str(e)}"


def chat_with_gemini(prompt: str, chat_history: List[Dict[str, str]]) -> str:
    try:
        # Format messages for Gemini
        history = []

        # Format messages fo Gemini 
        history = []
        for i in range(0, len(chat_history)-1, 2):
            if i + 1 < len(chat_history):
                user_msg = chat_history[i]
                assistant_msg = chat_history[i+1]
        
                if user_msg["role"] == "user" and assistant_msg["role"] == "assistant":
                    history.append({
                        "role": "user", 
                        "parts": [user_msg["content"]]}) 
            
                    history.append({"role": "model", 
                    "parts": [user_msg["content"]]})

        # Generative response for gemini
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        return response.text

    except Exception as e:
        return f"Error communicating with Gemini API: {str(e)}"


def chat_with_openai(prompt: str, chat_history: List[Dict[str, str]]) -> str:
    try:
        # Format messages for OpenAI
        messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})

        # Add current user prompt
        messages.append({"role": "user", "content": prompt})

        # Generative response for OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0.7, max_tokens=1024
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error communicating with OpenAI API: {str(e)}"


def main():
    init_db()

    if "is_authenticated" not in st.session_state or not st.session_state:
        login_page()
    else:
        chatbot_interface()

def chatbot_interface():
    st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
    st.title("🤖 AI Chatbot")

    # Initialize session state
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "curent_model" not in st.session_state:
        st.session_state.current_model = "gemini"
    
    # Sidebar for model selection
    with st.sidebar:
        st.title("Settings ⚙️")

        # Logout Button
        if st.button("Logout"):
            for key in ["username", "user_id", "is_authenticated", "chat_history", "session_id"]:
                if key in st.session_state:
                    st.session_state.pop(key)

            st.rerun()


        st.divider()

        # Model selection
        st.subheader("Choose AI Model")
        model_choice = st.radio(
            "Select AI Model",
            ["Gemini", "OpenAI"],
            format_func=lambda x: AI_MODELS[x.lower()],
            horizontal=True,
            index=0 if st.session_state.current_model == "gemini" else 1,
        )

        # Update current model if changed
        if model_choice != st.session_state.current_model:
            st.session_state.current_model = model_choice.lower()

        st.divider()

        # Recall feature
        st.subheader("Conversation Recall")

        recall_options = st.radio(
            "Recall Conversations from:", ["All Models", "Current Model Only"], index=0
        )

        if st.button("Summarize Recent Conversations"):
            with st.spinner("Generating summary..."):
                # Get recent conversations based on filter selection
                model_filter = (
                    None
                    if recall_options == "All Models"
                    else st.session_state.current_model
                )
                recent_convs = get_recent_conversations(
                    st.session_state.session_id, st.session_state.user_id, limit=5, model_filter=model_filter
                )

                # Generate Summary using current model
                summary = summarize_conversation(
                    recent_convs, st.session_state.current_model
                )   

                if recent_convs:
                    store_conversation_summary(
                        st.session_state.session_id,
                        recent_convs[0]["id"],
                        summary,
                        st.session_state.user_id
                    )

    st.divider()
            
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.session_id = datetime.datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )

    st.caption(f"Currently using: {AI_MODELS[st.session_state.current_model]}")

        # Chat input area
    with st.container():
        user_input = st.text_input("Type your message here...")

        if user_input:
            # Add user message to chat history
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input}
            )
            store_message(
                st.session_state.session_id,
                "user",
                user_input,
                st.session_state.current_model,
                st.session_state.user_id
            )

            # Get response from selected AI model
            with st.spinner("Thinking..."):
                response = chat_with_ai(
                    user_input,
                    st.session_state.chat_history,
                    st.session_state.current_model,
                )

            # Add assistant from seletced AI model
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response}
            )
            store_message(
                st.session_state.session_id,
                "assistant",
                response,
                st.session_state.current_model,
                st.session_state.user_id
            )
        
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
def login_page():
    st.title("🤖 AI Chatbot Login")
    
    # Check if this is the first run and we need to create an admin user
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    conn.close()
    
    if user_count == 0:
        st.info("Welcome to the first-time setup! Please create an admin account.")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_button = st.form_submit_button("Create Account")
            
            if signup_button:
                if not new_username or not new_password:
                    st.error("Please provide both username and password")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success = create_user(new_username, new_password)
                    if success:
                        st.success(f"Account created successfully! You can now log in as {new_username}")
                        st.session_state.username = new_username
                        st.session_state.is_authenticated = True
                        auth_success, user_id = authenticate_user(new_username, new_password)
                        if auth_success:
                            st.session_state.user_id = user_id
                            st.rerun()
                    else:
                        st.error("Username already exists. Please choose another one.")
    else:
        # Regular login form
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    if not username or not password:
                        st.error("Please provide both username and password")
                    else:
                        auth_success, user_id = authenticate_user(username, password)
                        if auth_success:
                            st.success(f"Welcome back, {username}!")
                            # Store authentication in session state
                            st.session_state.username = username
                            st.session_state.user_id = user_id
                            st.session_state.is_authenticated = True
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
        
        with tab2:
            with st.form("signup_form_regular"):
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                signup_button = st.form_submit_button("Create Account")
                
                if signup_button:
                    if not new_username or not new_password:
                        st.error("Please provide both username and password")
                    elif new_password != confirm_password:
                        st.error("Passwords don't match")
                    else:
                        success = create_user(new_username, new_password)
                        if success:
                            st.success(f"Account created successfully! You can now log in as {new_username}")
                        else:
                            st.error("Username already exists. Please choose another one.")

        


if __name__ == "__main__":
    main()
