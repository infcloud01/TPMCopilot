*Built with ❤️ by eXo Business Technologies.*

This is a simple **Quick Start Guide** designed for a T(echnical)PM who just wants to get the agent running.

# 🤖 TPM Copilot: The AI Co-pilot for TPMs

TPM Copilot is an open-source AI agent to help Technical Program Managers (TPMs) automate administrative overhead. Instead of clicking through endless menus, filters, and dropdowns, you can simply chat with your Jira board in plain English.

Powered by **LangChain**, **LangGraph**, and **OpenAI**.

## 🚀 What can it do?
*   **List Projects & Tickets:** "Show me all high priority bugs assigned to me."
*   **Update Statuses:** "Move ticket KAN-123 to Done."
*   **Assign Users:** "Assign KAN-123 to conrad@example.com."
*   **Change Dates:** "Update the due date for KAN-123 to next Friday."
*   **Add Comments:** "Add a comment to KAN-123 asking for a status update."
*   **Create Tickets:** "Create a task to Update Documentation."
*   **Delete Tickets:** "Delete ticket KAN-999."

---

## 📋 Prerequisites

Before you start, you need **Python installed** on your computer and two specific "Keys" (passwords) to allow the bot to talk to the cloud.

### 1. OpenAI API Key (The Brain)
*   Go to [OpenAI API Keys](https://platform.openai.com/api-keys).
*   Click **"Create new secret key."**
*   Copy the code (starts with `sk-...`).

### 2. Jira Cloud API Token (The Hands)
*   Go to [Atlassian Security](https://id.atlassian.com/manage-profile/security/api-tokens).
*   Click **"Create API token."**
*   Label it "JiraBot" and copy the code.
*   *Note: This is NOT your standard login password.*

---

## 🛠️ Installation

1.  **Download the Code:**
    Download the `tpmcopilot_v1.py` file to a folder on your computer (e.g., `Desktop/TPMCopilot`).

2.  **Open Terminal / Command Prompt:**
    *   **Mac:** `Cmd + Space` -> Type "Terminal"
    *   **Windows:** `Start` -> Type "cmd"

3.  **Install Requirements:**
    Copy and paste this command into your terminal to install the necessary libraries:
    ```bash
    pip install langchain langchain-openai langgraph atlassian-python-api
    ```

---

## ⚙️ Configuration: Set Your Project Key (Critical!)

By default, the `tpmcopilot_v1.py` script is set up to work with a demo project named **"KAN"**. You likely have a different Project Key (e.g., "PROJ", "ENG", "OPS").

**How to find your Key:** Look at any existing ticket in your project (e.g., `ABC-123`). The letters before the hyphen (`ABC`) are your Key.

**You must update the code in these 2 places:**

1.  **The Brain (System Prompt):**
    *   Open `tpmcopilot_v1.py` in a text editor (Notepad, TextEdit, VS Code).
    *   Search for the function `def get_system_message():`.
    *   Change the line: `- **Project Key:** KAN` to your actual key.
    *   *Why?* This tells the AI which project to search by default.

2.  **The Hands (Create Tool):**
    *   Search for the function `def create_ticket`.
    *   Change the line: `'project': {'key': 'KAN'},` to your actual key.
    *   *Why?* This ensures new tickets are created in the correct board.

---

## ▶️ How to Run

1.  **Navigate to your folder:**
    In your terminal, type `cd` followed by the path to your folder.
    ```bash
    cd Desktop/TPMCopilot
    ```

2.  **Start the Bot:**
    ```bash
    python tpmcopilot_v1.py
    ```

3.  **Authenticate:**
    The bot will ask for your **OpenAI Key** and **Jira Token**. Paste them in.
    *   *Security Note: You won't see the text appear on screen as you paste your keys. This is normal. Just paste and hit Enter.*

---

## 🗣️ Example Commands

Once the bot says **"🤖 TPM Copilot is ready!"**, try these:

*   **Search:** "List all tickets in the Backlog."
*   **Search (Advanced):** "Show me tickets assigned to me that are blocked."
*   **Details:** "What is the latest status of PROJ-123?"
*   **Action:** "Assign PROJ-123 to me."
*   **Action:** "Add a comment to PROJ-55 saying 'I am working on this today'."
*   **Action:** "Create a new Bug called 'Login Error' with description 'User cannot sign in on mobile'."

---

## ❓ Troubleshooting

*   **"User not found" when assigning:**
    *   Try using the user's email address instead of their name.
    *   Ensure the user has been added to the Project in Jira Settings.
*   **"Project not found":**
    *   Did you update the "KAN" key in the configuration step above?
*   **"401 Unauthorized":**
    *   Your Jira Token or Email is incorrect. Ensure you are using the specific API Token from the Atlassian link above, not your password.
