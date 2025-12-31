##############################################
# Built with ❤️ by eXo Business Technologies #
############# TPMCOPILOT.COM ##################
import os
import getpass
import inspect
import requests
from datetime import datetime
from typing import Annotated, TypedDict

# Third-party libraries
from atlassian import Jira
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# ==========================================
# 1. AUTHENTICATION & CONFIGURATION
# ==========================================
print("--- JIRA BOT SETUP ---")

# A. OpenAI Setup
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter OpenAI API Key: ")

# B. Jira Cloud Setup
# Replace these with your actual details or leave as is to be prompted
JIRA_URL = "https://your-domain.atlassian.net/" # <--- UPDATE THIS WITH YOUR CLOUD URL
JIRA_EMAIL = "your-email@email.com"          # <--- UPDATE THIS WITH THE EMAIL YOU LOG INTO JIRA CLOUD WITH

if "your-domain" in JIRA_URL:
    JIRA_URL = input("Enter Jira Cloud URL (e.g., https://xyz.atlassian.net): ").strip()
if "your-email" in JIRA_EMAIL:
    JIRA_EMAIL = input("Enter Jira Login Email: ").strip()

JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
if not JIRA_API_TOKEN:
    print("Note: Generate Token at https://id.atlassian.com/manage-profile/security/api-tokens")
    JIRA_API_TOKEN = getpass.getpass("Enter Jira Cloud API Token: ").strip()

# Initialize Jira Client (CLOUD VERSION)
try:
    jira = Jira(
        url=JIRA_URL,
        username=JIRA_EMAIL,
        password=JIRA_API_TOKEN,
        cloud=True  # Required for Cloud
    )
    # Quick connectivity check
    user = jira.myself()
    print(f"✅ Connected to Jira as: {user['displayName']}")
except Exception as e:
    print(f"❌ Jira Connection Failed: {e}")
    exit(1)

# ==========================================
# 2. DEFINE TOOLS
# ==========================================

@tool
def list_projects():
    """
    Retrieves a list of all Jira projects visible to the user.
    Use this to find Project Keys.
    """
    try:
        projects = jira.projects()
        simplified = [f"{p['name']} (Key: {p['key']})" for p in projects]
        return "\n".join(simplified) if simplified else "No projects found."
    except Exception as e:
        return f"Error listing projects: {str(e)}"

@tool
def list_jiras(jql_query: str):
    """
    Searches for tickets using JQL (Jira Query Language).
    Examples:
    - "project = KAN AND priority = High"
    - "assignee = currentUser() AND resolution = Unresolved"
    """
    try:
        results = jira.jql(jql_query, limit=10)
        issues = results.get("issues", [])
        if not issues:
            return "No tickets found matching that query."
        
        summary_list = []
        for issue in issues:
            fields = issue['fields']
            summary_list.append(
                f"[{issue['key']}] {fields['summary']} "
                f"(Status: {fields['status']['name']}, Priority: {fields['priority']['name']})"
            )
        return "\n".join(summary_list)
    except Exception as e:
        return f"JQL Error: {str(e)}"

@tool
def get_ticket_details(ticket_id: str):
    """Retrieves full details for a specific ticket (e.g., KAN-123)."""
    try:
        issue = jira.issue(ticket_id)
        f = issue['fields']
        return (
            f"Key: {issue['key']}\n"
            f"Summary: {f['summary']}\n"
            f"Status: {f['status']['name']}\n"
            f"Priority: {f['priority']['name']}\n"
            f"Assignee: {f['assignee']['displayName'] if f['assignee'] else 'Unassigned'}\n"
            f"Due Date: {f['duedate']}\n"
            f"Description: {f['description']}"
        )
    except Exception as e:
        return f"Error getting ticket {ticket_id}: {str(e)}"

@tool
def update_ticket_status(ticket_id: str, new_status: str):
    """Updates the status of a ticket (e.g., 'Done', 'In Progress')."""
    try:
        jira.set_issue_status(ticket_id, new_status)
        return f"Successfully updated {ticket_id} to {new_status}."
    except Exception as e:
        return f"Error updating status: {str(e)}"

@tool
def update_due_date(ticket_id: str, date_str: str):
    """Updates due date. date_str must be 'YYYY-MM-DD'."""
    try:
        jira.update_issue_field(ticket_id, {'duedate': date_str})
        return f"Successfully updated due date of {ticket_id} to {date_str}."
    except Exception as e:
        return f"Error updating date: {str(e)}"

@tool
def create_ticket(summary: str, issue_type: str = "Task", description: str = ""):
    """
    Creates a new ticket in the KAN project.
    """
    try:
        issue_dict = {
            'project': {'key': 'KAN'}, # <--- HARDCODE FOR YOUR WORKFLOW
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type},
        }
        new_issue = jira.create_issue(fields=issue_dict)
        return f"Created ticket {new_issue['key']}: {summary}"
    except Exception as e:
        return f"Error creating ticket: {str(e)}"

@tool
def assign_ticket(ticket_id: str, assignee_name: str):
    """
    Assigns a Jira ticket to a specific user.
    """
    try:
        # 1. Handle Unassign
        if assignee_name.lower() in ["unassigned", "nobody", "remove"]:
            jira.assign_issue(ticket_id, None)
            return f"Successfully unassigned ticket {ticket_id}."

        account_id = None
        display_name = assignee_name

        # 2. Handle "Assign to Me"
        if assignee_name.lower() in ["me", "myself", "self", "currentuser()"]:
            print("DEBUG: Fetching 'myself' details...")
            myself = jira.myself()
            account_id = myself['accountId']
            display_name = myself['displayName']
        
        # 3. Handle specific name/email search via Direct API
        else:
            print(f"DEBUG: specific search for '{assignee_name}' on ticket {ticket_id}...")
            
            # --- DIRECT API CALL START ---
            # We hit the endpoint manually to avoid "AttributeError"
            endpoint = "rest/api/3/user/assignable/search"
            params = {
                'issueKey': ticket_id,
                'query': assignee_name,
                'maxResults': 5
            }
            # This uses the underlying request session of the jira object
            candidates = jira.get(endpoint, params=params)
            # --- DIRECT API CALL END ---

            print(f"DEBUG: Found {len(candidates)} candidates.")
            
            if not candidates:
                return (
                    f"Could not find a user matching '{assignee_name}' who is allowed to be assigned to {ticket_id}. "
                    "Please ensure they are added to the project."
                )

            # Pick the first match
            user = candidates[0]
            account_id = user['accountId']
            display_name = user['displayName']

        # 4. Perform Assignment
        print(f"DEBUG: Assigning to '{display_name}' (ID: {account_id})")
        
        # We also do the update manually to be safe
        jira.update_issue_field(ticket_id, {'assignee': {'id': account_id}})
        
        return f"Successfully assigned {ticket_id} to {display_name}."

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return f"Failed to assign ticket. Error details: {str(e)}"

@tool
def add_comment(ticket_id: str, comment_body: str):
    """
    Adds a comment to a Jira ticket.
    
    Args:
        ticket_id: The key of the ticket (e.g., "KAN-123").
        comment_body: The text content of the comment.
    """
    try:
        print(f"DEBUG: Adding comment to {ticket_id}...")
        
        # The library wrapper handles the API call
        jira.issue_add_comment(ticket_id, comment_body)
        
        return f"Successfully added comment to {ticket_id}."
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return f"Failed to add comment. Error: {str(e)}"

@tool
def delete_ticket(ticket_id: str):
    """
    Deletes a Jira ticket permanently.
    WARNING: This action is irreversible. Use with caution.
    """
    try:
        print(f"DEBUG: Attempting to DELETE ticket {ticket_id}...")
        
        # The library method handles the API call
        # 'recursive=False' means it might fail if the ticket has subtasks.
        # Usually, simple tasks/bugs delete fine.
        jira.delete_issue(ticket_id)
        
        return f"Successfully deleted ticket {ticket_id}."
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return f"Failed to delete ticket {ticket_id}. Error: {str(e)}"

@tool
def link_tickets(source_ticket: str, target_ticket: str, link_type: str = "Blocks") -> str:
    """
    Links two tickets together.
    
    Args:
        source_ticket: The ticket that is affecting the other (e.g., KAN-1).
        target_ticket: The ticket being affected (e.g., KAN-2).
        link_type: The type of link (e.g., "Blocks", "Relates", "Clones"). 
                   Defaults to "Blocks".
    """
    try:
        print(f"DEBUG: Linking {source_ticket} -> {link_type} -> {target_ticket}")

        # Construct the dictionary payload expected by your specific library
        link_payload = {
            "type": {
                "name": link_type
            },
            "inwardIssue": {
                "key": source_ticket
            },
            "outwardIssue": {
                "key": target_ticket
            }
        }

        # Pass the dictionary as the single positional argument
        jira.create_issue_link(link_payload)
        
        return f"Successfully linked {source_ticket} to {target_ticket} with type '{link_type}'."
        
    except Exception as e:
        return f"Error linking tickets: {e}"

@tool
def unlink_tickets(source_ticket: str, target_ticket: str) -> str:
    """
    Removes the link between two Jira tickets.
    """
    try:
        print(f"DEBUG: searching for link between {source_ticket} and {target_ticket}")
        
        # 1. GET THE ISSUE
        # We know this returns a Dictionary based on your logs
        source_issue = jira.issue(source_ticket)
        
        # 2. EXTRACT LINKS
        # Using dictionary access as confirmed by your previous success
        fields = source_issue.get('fields', {})
        links = fields.get('issuelinks', [])

        link_id_to_delete = None

        # 3. FIND THE LINK ID
        for link in links:
            # Check Outward (Source -> Target)
            if 'outwardIssue' in link and link['outwardIssue']['key'] == target_ticket:
                link_id_to_delete = link['id']
                print(f"DEBUG: Found outward link ID: {link_id_to_delete}")
                break
            
            # Check Inward (Target -> Source)
            if 'inwardIssue' in link and link['inwardIssue']['key'] == target_ticket:
                link_id_to_delete = link['id']
                print(f"DEBUG: Found inward link ID: {link_id_to_delete}")
                break
        
        if not link_id_to_delete:
            return f"No active link found between {source_ticket} and {target_ticket}."

        # 4. DELETE USING API
        # Since the library lacks the method, we hit the API directly.
        print(f"DEBUG: Deleting Link ID {link_id_to_delete} via API")
        
        api_endpoint = f"{JIRA_URL}/rest/api/3/issueLink/{link_id_to_delete}"
        
        response = requests.delete(
            api_endpoint,
            auth=(JIRA_EMAIL, JIRA_API_TOKEN),
            headers={"Content-Type": "application/json"}
        )
        
        # 204 = No Content (Successful Deletion), 200 is also possible sometimes
        if response.status_code in [200, 204]:
            return f"Successfully unlinked {source_ticket} and {target_ticket}."
        else:
            return f"Failed to delete link via API. Status: {response.status_code}, Error: {response.text}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error unlinking tickets: {e}"

@tool
def get_ticket_comments(ticket_id: str):
    """
    Retrieves the comments for a specific ticket.
    Use this to understand the history or discussion behind a ticket.
    """
    try:
        # Get comments (returns a list of dicts)
        comments_data = jira.issue_get_comments(ticket_id)
        comments = comments_data.get('comments', [])
        
        if not comments:
            return f"No comments found for {ticket_id}."
            
        # Format them nicely
        history = []
        for c in comments[-5:]: # Limit to last 5 to save tokens
            author = c['author']['displayName']
            body = c['body']
            # Truncate long comments
            if len(body) > 200: 
                body = body[:200] + "..."
            history.append(f"- {author}: {body}")
            
        return "\n".join(history)
    except Exception as e:
        return f"Failed to get comments. Error: {str(e)}"

@tool
def add_to_epic(issue_keys: list, epic_key: str):
    """
    Adds a list of issues to an Epic.
    
    Args:
        issue_keys: A list of strings, e.g. ["KAN-18", "KAN-19"]
        epic_key: The key of the Epic ticket, e.g. "KAN-1"
    """
    success_count = 0
    errors = []

    # Handle case where LLM passes a single string instead of a list
    if isinstance(issue_keys, str):
        issue_keys = [issue_keys]

    print(f"DEBUG: Adding {issue_keys} to Epic {epic_key} via 'parent' field...")

    for issue in issue_keys:
        try:
            # In Jira Cloud v3, assigning to an Epic is done by setting the 'parent' field.
            # This works for both Team-Managed and Company-Managed projects in most modern instances.
            jira.update_issue_field(issue, {'parent': {'key': epic_key}})
            success_count += 1
            print(f"DEBUG: Successfully moved {issue} to {epic_key}")
            
        except Exception as e:
            print(f"DEBUG ERROR on {issue}: {e}")
            errors.append(f"{issue}: {str(e)}")

    if errors:
        return f"Partial success. Added {success_count} tickets. Failed on: {', '.join(errors)}"
        
    return f"Successfully added {len(issue_keys)} tickets to Epic {epic_key}."


# List of tools provided to the LLM
tools = [list_projects,
         list_jiras,
         get_ticket_details,
         update_ticket_status,
         update_due_date,
         create_ticket,
         assign_ticket,
         add_comment,
         delete_ticket,
         link_tickets,
         unlink_tickets,
        get_ticket_comments,
        add_to_epic]

# ==========================================
# 3. AGENT SETUP (LLM & GRAPH)
# ==========================================

# Initialize LLM with longer timeout
llm = ChatOpenAI(model="gpt-4o", temperature=0, request_timeout=120)
llm_with_tools = llm.bind_tools(tools)

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# System Prompt
def get_system_message():
    date_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""You are an expert Technical Program Manager (TPM) assistant for the 'Jirabot' project.

CONTEXT:
- **Project Key:** KAN
- **Current Date:** {date_str}

RULES:
1. Unless asked otherwise, scope all JQL searches to 'project = KAN'.
2. If the user gives a relative date (e.g., "next Friday"), calculate the YYYY-MM-DD format.
3. Be concise and professional.
4. **SAFETY:** Before calling 'delete_ticket', ensure the user explicitly provided the ticket ID. Do not guess.
"""
    return SystemMessage(content=prompt)

# Node: Agent (The Brain)
def agent_node(state: AgentState):
    sys_msg = get_system_message()
    # Prepend system message to history
    messages = [sys_msg] + state["messages"]
    result = llm_with_tools.invoke(messages)
    return {"messages": [result]}

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

react_graph = builder.compile()

# ==========================================
# 4. MAIN CHAT LOOP
# ==========================================

def chat():
    print("\n🤖 TPM Copilot is ready! (Type 'quit' to exit)")
    print("Example: 'List my high priority tickets' or 'Create a task to update docs'")
    
    # Simple memory for this session
    conversation_history = []

    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            # Prepare state
            conversation_history.append(HumanMessage(content=user_input))
            
            # Stream response
            events = react_graph.stream(
                {"messages": conversation_history},
                stream_mode="values"
            )
            
            for event in events:
                if "messages" in event:
                    msg = event["messages"][-1]
                    if msg.type == "ai":
                        # Only print final AI response, not tool calls (keeps it clean)
                        if not msg.tool_calls:
                            print(f"Agent: {msg.content}")
                            conversation_history.append(msg)
                    elif msg.type == "tool":
                        # Optional: Print tool output for debugging
                        # print(f"[System] Tool Output: {msg.content}")
                        pass
                        
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    chat()
