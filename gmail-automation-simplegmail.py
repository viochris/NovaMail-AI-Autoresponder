# --- Standard Python Libraries ---
import base64
import os
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- Third-Party Utility Libraries ---
import requests
from dotenv import load_dotenv

# --- Core Application Libraries (Email & AI) ---
from google import genai
from simplegmail import Gmail

# ==============================================================================
# ENVIRONMENT VARIABLES & CONFIGURATION
# ==============================================================================
# Load sensitive credentials from the local .env file securely
load_dotenv()

# Fetch configuration keys from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ==============================================================================
# DYNAMIC CREDENTIAL GENERATOR FOR CLOUD DEPLOYMENT (RAILWAY)
# ==============================================================================
# simplegmail requires physical 'credentials.json' and 'gmail_token.json' files.
# For security, these files are .gitignored and should NEVER be pushed to GitHub.
# This script generates them on the cloud server dynamically from Environment Variables.

# # 1. Generate 'credentials.json' on the server
# creds_env = os.getenv("GMAIL_CREDENTIALS")
# if creds_env and not os.path.exists("credentials.json"):
#     with open("credentials.json", "w") as f:
#         f.write(creds_env)

# 2. Generate 'gmail_token.json' on the server (Requires running locally once first)
token_env = os.getenv("GMAIL_TOKEN")
if token_env and not os.path.exists("gmail_token.json"):
    with open("gmail_token.json", "w") as f:
        f.write(token_env)

# ==============================================================================
# INITIALIZE CLIENTS
# ==============================================================================
# Initialize Google Gemini Client
client = genai.Client(api_key=GOOGLE_API_KEY)

# Initialize SimpleGmail Client (Requires client_secret.json in root dir)
gmail = Gmail()

print("🎧 NovaMail AI (Polling Mode) is listening to your Inbox...")

# ==============================================================================
# MAIN POLLING LOOP
# ==============================================================================
while True:
    try:
        # 1. Fetch unread emails
        unread_messages = gmail.get_unread_messages()

        if not unread_messages:
            print("📭 Inbox is clean. (Checking again in 30 seconds)")
        else:
            # 2. Process each unread email
            for msg in unread_messages:
                # Define the WIB timezone (UTC+7) for accurate local timestamping
                wib_tz = timezone(timedelta(hours=7))
                
                try:
                    # Parse the ISO 8601 formatted date string provided by simplegmail into a datetime object.
                    # Wrapping in str() acts as a defensive safeguard against unexpected data types.
                    parsed_email_date = datetime.fromisoformat(str(msg.date))
                    
                    # Convert the timezone-aware date to the WIB timezone and apply a consistent readable format
                    received_time_wib = parsed_email_date.astimezone(wib_tz).strftime("%Y-%m-%d %H:%M:%S WIB")
                except Exception as e:
                    # Fallback to the raw string value to ensure the application continues running if parsing fails
                    received_time_wib = str(msg.date)

                # --- PREPARE TERMINAL PREVIEW ---
                # Create a concise 100-character snippet for terminal logging
                body_preview = f"{msg.plain[:100]}..." if len(msg.plain) > 100 else msg.plain

                print("\n==================================================")
                print(f"📩 NEW EMAIL DETECTED!")
                print(f"🕒 Date   : {received_time_wib}")
                print(f"👤 From   : {msg.sender}")
                print(f"📌 Subject: {msg.subject}")
                print(f"💬 Body   : {body_preview}") # Print first 100 chars for context
                print("==================================================")

                # 3. Generate Reply using Gemini AI
                # Enhanced prompt to give the AI a clear persona, context, and strict instructions
                ai_prompt = (
                    f"You are an intelligent and highly professional email assistant. "
                    f"Your task is to draft a polite, concise, and contextually appropriate reply to the following incoming email.\n\n"
                    f"--- EMAIL DETAILS ---\n"
                    f"Date Received: {received_time_wib}\n"
                    f"From: {msg.sender}\n"
                    f"Subject: {msg.subject}\n"
                    f"Message (May include previous conversation history):\n{msg.plain}\n\n"
                    f"--- INSTRUCTIONS ---\n"
                    f"1. Analyze the 'Message' section. Focus on replying to the newest message at the top, using any quoted text below it purely as context.\n"
                    f"2. Acknowledge the sender's latest message gracefully.\n"
                    f"3. Provide a clear, relevant, and helpful response based on the context of their message.\n"
                    f"4. Maintain a warm yet professional tone.\n"
                    f"5. Output ONLY the email body text. Do not include subject lines or conversational filler like 'Here is your draft'."
                )

                print("🤖 Gemini is thinking...")
                
                # SECURE AI INVOCATION: Wrapped in try-except to prevent API crashes
                try:
                    model_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=ai_prompt
                    )

                    # 4. Validate AI Output
                    if model_response.text and len(model_response.text.strip()) > 0:
                        reply_text = model_response.text.strip()
                    else:
                        reply_text = "Apologies, I received your email but the AI failed to generate a response at this time."

                except Exception as ai_error:
                    # SECURE ERROR HANDLING: Sanitize output to prevent API Key leakage
                    error_str = str(ai_error).lower()
                    if "quota" in error_str or "429" in error_str:
                        print("❌ AI Error: API Quota exceeded or Rate Limited.")
                    elif "api_key" in error_str or "403" in error_str:
                        print("❌ AI Error: API Key is invalid or expired.")
                    else:
                        print("❌ AI Error: Failed to generate content due to an unknown API issue.")
                    
                    # Fallback text so the bot can still reply and move past the broken email
                    reply_text = "System Notice: The AI assistant is currently unavailable to process this request. We will get back to you manually."

                # 5. Send Reply & Update Email Status
                # Ensure the reply subject follows standard email thread conventions (adding "Re:" if not present)
                reply_subject = msg.subject if msg.subject.startswith("Re:") else f"Re: {msg.subject}"

                # Construct the MIME message container to build a compliant RFC 2822 email structure
                mime_msg = MIMEMultipart()
                mime_msg["to"] = msg.sender
                mime_msg["from"] = "me"
                mime_msg["subject"] = reply_subject

                # Retrieve the original Message-ID from headers to maintain thread integrity
                # We check both standard and lowercase keys for maximum compatibility
                original_message_id = (
                    msg.headers.get("Message-ID") or 
                    msg.headers.get("message-id")
                )

                # Fetch existing references to track the entire conversation history
                references = (
                    msg.headers.get("References") or
                    msg.headers.get("references")
                )

                # Inject threading headers to ensure Gmail and other clients group the reply correctly
                if original_message_id:
                    # In-Reply-To links this specific reply to the parent message
                    mime_msg["In-Reply-To"] = original_message_id

                    # References maintains the chain of all previous Message-IDs in the conversation
                    if references:
                        # Append the current message ID to the existing reference chain
                        mime_msg["References"] = references + " " + original_message_id
                    else:
                        # Start a new reference chain if none exists
                        mime_msg["References"] = original_message_id

                # Attach the AI-generated reply body as HTML for rich text rendering
                mime_msg.attach(MIMEText(reply_text.replace("\n", "<br>"), "html", "utf-8"))

                # Encode the entire MIME structure into a URL-safe Base64 string for Gmail API compatibility
                raw_string = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

                # Prepare the API payload consisting of the encoded raw message and the existing threadId
                raw_payload = {
                    "raw": raw_string,
                    "threadId": msg.thread_id
                }
                
                # Dispatch the reply directly through the official Google Gmail API service layer
                gmail.service.users().messages().send(userId='me', body=raw_payload).execute()
                
                # Mark the original message as read to signify successful processing
                msg.mark_as_read()
                print("✅ Email successfully replied and marked as READ.")

                # ==============================================================================
                # TELEGRAM NOTIFICATION SYSTEM
                # ==============================================================================
                if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
                    print("⚠️ Warning: Telegram credentials are missing. Skipping notification.")
                    continue

                # Fetch the current exact time in WIB for the AI reply timestamp
                current_time = datetime.now(wib_tz).strftime("%Y-%m-%d %H:%M:%S WIB")

                # Create a more detailed 500-character snippet for the Telegram report
                # This ensures the report stays within Telegram's 4096 character limit
                body_preview = f"{msg.plain[:500]}..." if len(msg.plain) > 500 else msg.plain

                # Prepare a well-formatted Markdown report for Telegram.
                # Truncating the original message body to 500 chars to avoid Telegram's 4096 character limit.
                telegram_report = (
                    f"🚨 *NOVAMAIL AI REPORT* 🚨\n\n"
                    f"🕒 *Received:* `{received_time_wib}`\n"
                    f"👤 *From:* `{msg.sender}`\n"
                    f"📌 *Subject:* {msg.subject}\n\n"
                    f"💬 *Original Message:*\n{body_preview}\n\n"
                    f"🤖 *AI Reply Sent:*\n_{reply_text}_\n\n"
                    f"⏱️ *Replied At:* `{current_time}`"
                )

                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                data = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": telegram_report,
                    "parse_mode": "Markdown"
                }

                try:
                    # Send POST request to Telegram API
                    response = requests.post(url, json=data)
                    
                    # Check HTTP Status Code (200 = OK)
                    if response.status_code == 200:
                        print("📱 Success: Notification sent to Telegram!")
                    else:
                        # Log the specific error from Telegram for debugging safely
                        print(f"❌ Telegram API Refused: Status Code {response.status_code}")
                        
                except Exception as e:
                    # SAFE ERROR HANDLING
                    # Preventing the 'url' variable (containing the token) from leaking in the logs.
                    error_str = str(e).lower()

                    if "connection" in error_str or "dns" in error_str:
                        print("❌ Network Error: Failed to connect to Telegram API.")
                    elif "timeout" in error_str:
                        print("⏳ Timeout Error: Telegram API did not respond.")
                    elif "ssl" in error_str:
                        print("🔒 SSL Error: Certificate verification failed.")
                    else:
                        print("❌ Telegram Send Failed: Unknown network error occurred.")

    except Exception as general_error:
        # SECURE ERROR HANDLING: Do NOT print raw 'general_error' to avoid credential leaks.
        error_str = str(general_error).lower()
        if "credentials" in error_str or "token" in error_str:
            print("🚨 System Error: Authentication failed. Check your token.json or credentials.")
        else:
            print(f"🚨 An unexpected system error occurred. Waiting for the next polling cycle to retry -> {error_str}.")

    # ==============================================================================
    # POLLING DELAY
    # ==============================================================================
    # Pause for 30 seconds before checking the inbox again to avoid rate-limiting
    time.sleep(30)
