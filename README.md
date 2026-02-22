# 📧 NovaMail AI: Automated Gmail Autoresponder (Gemini + Telegram Edition)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![Gmail API](https://img.shields.io/badge/Gmail%20API-EA4335?logo=gmail&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Notifier-2CA5E0?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

> 🛑 **CUSTOMIZATION NOTICE**  
> **This script is built as a General-Purpose Autoresponder.** Because the AI is instructed with a broad and professional persona, some generated replies might sound slightly generic or template-like. **For specific business use cases (e.g., customer service, sales inquiries, specific brand tone), you are highly encouraged to modify the `ai_prompt` variable inside the script to suit your exact needs.**

## 📌 Overview
**NovaMail AI** is an intelligent, fully automated background service that acts as your personal email assistant. 

Powered by **Google Gemini 2.5 Flash** and the **Gmail API**, this script continuously monitors your inbox for unread messages. Upon detecting a new email, it reads the context (including previous thread history), generates a polite and contextually accurate professional reply, sends it automatically while maintaining strict email threading integrity, and instantly delivers a detailed execution report directly to your Telegram.

## ✨ Key Features

### 🧠 Context-Aware AI Generation
Utilizes Gemini 2.5 Flash to analyze incoming emails. The system prompt is engineered to distinguish between the newest message and older quoted thread history, ensuring the AI replies to the correct context without hallucinations.

### 🧵 Strict Thread Integrity (RFC 2822 Compliance)
Unlike basic email bots that create messy, fragmented inboxes, NovaMail constructs advanced MIME payloads. By extracting and injecting original `Message-ID` and `References` headers, it guarantees that AI replies stack perfectly within the original email conversation thread.

### 📱 Real-Time Telegram Reporting
Never miss what your bot is doing. Every time an email is processed and replied to, the system fires a well-formatted Markdown webhook to your personal Telegram chat, displaying the sender, the original message snippet, and the exact AI reply sent.

### 🛡️ Defensive Programming & Resilience
Built with robust `try-except` blocks to handle API rate limits (HTTP 429), token expirations, and timezone parsing anomalies (ISO 8601 vs RFC formats). If the AI fails, a graceful fallback mechanism ensures the system doesn't crash.

## 🛠️ Tech Stack
* **LLM Engine:** Google Gemini 2.5 Flash (`google-genai`).
* **Email Client Integration:** `simplegmail` & Official Google API Client.
* **Notification System:** Telegram Bot API (via raw `requests`).
* **Message Formatting:** Python Standard Libraries (`email.mime`, `base64`).

## ⚠️ Limitations & Disclaimers

### 1. General Template Persona
As mentioned above, the default AI prompt is designed to be highly professional but generalized. To maximize its potential, adjust the `ai_prompt` string in the code to inject your own specific knowledge base, pricing lists, or personal calendar links.
### 2. API Quota Consumption
This script polls your inbox every 30 seconds. While polling the Gmail API is lightweight, every unread email triggers a request to the Gemini API. A sudden influx of emails (e.g., spam bombs or newsletters) could quickly exhaust your daily Gemini free-tier token limits. 
### 3. Server Deployment (Authentication)
This application relies on `credentials.json` (Google OAuth 2.0 Client IDs). For the first run, it requires manual user authorization via a web browser to generate `token.json`. Therefore, it must be initialized locally before deploying the `token.json` to a headless cloud server (like Railway or VPS).
### 4. Zero-Memory Architecture
This is a stateless script. It relies entirely on the email's physical body text (which usually contains the quoted previous messages) to understand context. It does not store past emails in an SQL database.

## 📦 Installation & Deployment

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/viochris/NovaMail-AI-Autoresponder.git
    cd NovaMail-AI-Autoresponder
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Local Environment Setup (`.env`)**
    Create a `.env` file in the root directory:
    ```env
    TELEGRAM_TOKEN=your_telegram_bot_token
    TELEGRAM_CHAT_ID=your_personal_telegram_id
    GOOGLE_API_KEY=your_gemini_api_key
    ```

4.  **Google OAuth Setup**
    * Go to Google Cloud Console.
    * Enable the **Gmail API**.
    * Create an OAuth 2.0 Client ID (Desktop App).
    * Download the JSON file and rename it exactly to `credentials.json`. Place it in the root folder.

5.  **Run Locally (First Initialization)**
    ```bash
    python gmail-automation-simplegmail.py
    ```
    *(Note: On the first run, a browser window will open asking you to log into your Google Account to authorize the app. Once authorized, it will create a `token.json` file).*

### 🖥️ Expected Terminal Output
```text
🎧 NovaMail AI (Polling Mode) is listening to your Inbox...
📭 Inbox is clean. (Checking again in 30 seconds)

==================================================
📩 NEW EMAIL DETECTED!
🕒 Date   : 2026-02-22 13:45:10 WIB
👤 From   : client@example.com
📌 Subject: Tanya Penawaran Jasa
💬 Body   : Halo, saya ingin menanyakan harga pembuatan website...
==================================================
🤖 Gemini is thinking...
✅ Email successfully replied and marked as READ.
📱 Success: Notification sent to Telegram!

```

---

**Authors:** Silvio Christian, Joe
*"Automate your inbox. Experience intelligent email management."*
