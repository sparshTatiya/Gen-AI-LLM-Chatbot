## How to Use

1. **Login/Register**: 
   - First-time setup will prompt you to create an admin account
   - Subsequent users can register for new accounts or log in with existing credentials

2. **Choose AI Model**: Select either Gemini or OpenAI in the sidebar radio buttons to choose which AI model to interact with.

3. **Chat Interface**: Type your messages in the chat input at the bottom of the screen.

4. **Model Switching**: You can switch between models at any time - your conversation history remains visible while the responses will come from the newly selected model.

5. **Recall Feature**: 
   - Choose whether to summarize conversations from "All Models" or "Current Model Only"
   - Click the "Summarize Recent Conversations" button to generate a summary

6. **Clear Chat**: Use the "Clear Chat" button to start a new conversation session.

7. **Logout**: Click the Logout button in the sidebar when you're done using the application.# Dual-Mode AI Chatbot with SQLite and Streamlit

This project implements a smart conversational chatbot using:
- **Google's Gemini AI API** and **OpenAI's GPT API** for natural language processing
- **SQLite** for conversation storage and retrieval
- **Streamlit** for the user interface

## Features

- User authentication system with secure password hashing
- Multiple user accounts with isolated conversation histories
- Dual-mode conversational interface (switch between Gemini and OpenAI)
- Persistent storage of all conversations in SQLite with model tracking
- Recall and summarize the last five conversations (filter by model or view all)
- Session-based conversation management
- Clean and responsive Streamlit interface
- Seamless model switching without losing context

## Setup Instructions

### 1. Prerequisites

Make sure you have Python 3.8+ installed. Then install the required packages:

```bash
pip install streamlit google-generativeai sqlite3 python-dotenv
```

### 2. Get API Keys

#### For Gemini:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an account if you don't have one
3. Generate a new API key

#### For OpenAI:
1. Go to [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Create an account if you don't have one
3. Generate a new API key

### 3. Configuration

The API keys are pre-configured in the application. Make sure your `.env` file contains:

```
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Note**: The API keys are embedded in the application and users do not need to enter them manually.

### 4. Run the Application

Start the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your default web browser, typically at `http://localhost:8501`.

## How to Use

1. **Choose AI Model**: Select either Gemini or OpenAI in the sidebar radio buttons to choose which AI model to interact with.

2. **Chat Interface**: Type your messages in the chat input at the bottom of the screen.

3. **Model Switching**: You can switch between models at any time - your conversation history remains visible while the responses will come from the newly selected model.

4. **Recall Feature**: 
   - Choose whether to summarize conversations from "All Models" or "Current Model Only"
   - Click the "Summarize Recent Conversations" button to generate a summary

5. **Clear Chat**: Use the "Clear Chat" button to start a new conversation session.

6. **API Configuration**: If needed, update your Gemini and OpenAI API keys in the "API Configuration" expander in the sidebar.

## How It Works

### Conversation Storage

- Each user session creates a unique session ID
- Messages are stored in SQLite with timestamps and role information
- Conversations are organized hierarchically for easy retrieval

### Summary Generation

When you click the "Summarize Recent Conversations" button:
1. The app retrieves your most recent conversations from the database
2. It prompts the Gemini model to generate a concise summary
3. The summary is displayed and also stored in the database for future reference

### Database Schema

The application uses two main tables:
- `conversations`: Stores session IDs, model used, and conversation metadata
- `messages`: Stores individual messages with references to their conversations

The database schema allows for filtering conversations by AI model, making it easy to compare performance or manage conversations from different providers.

## Customization

You can modify the following aspects of the chatbot:
- Gemini model version in `genai.GenerativeModel('gemini-pro')`
- OpenAI model version in `model="gpt-3.5-turbo"` (can upgrade to GPT-4 if needed)
- Number of recalled conversations in `limit` parameter of `get_recent_conversations()`
- UI elements in the Streamlit interface
- Add additional AI models by extending the pattern used for Gemini and OpenAI

## Troubleshooting

- **API Key Issues**: Verify your API keys are correct in the .env file or enter them directly in the sidebar
- **Database Errors**: If you encounter database issues, try deleting the `chatbot.db` file and restarting
- **Model Limitations**: Be aware of both Gemini and OpenAI APIs' usage limits and response guidelines
- **Switching Models**: If switching between models causes unexpected behavior, try clearing the chat and starting fresh

## Future Enhancements

Potential improvements for this chatbot:
- Add authentication system
- Implement conversation tagging and categorization
- Add option to export conversations
- Create visualization of conversation patterns
- Implement memory management for longer contexts
