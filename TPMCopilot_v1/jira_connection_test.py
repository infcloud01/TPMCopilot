#Use this to test you have a working Jira connection
import getpass
from atlassian import Jira
import requests

print("--- JIRA CLOUD CONNECTION TEST ---")

# 1. INPUTS
# Please enter these manually when running to ensure no stale variables exist.
url = input("Enter Jira URL (e.g., https://your-domain.atlassian.net): ").strip()
email = input("Enter your Email (used for Jira login): ").strip()
token = getpass.getpass("Enter your Jira Cloud API Token: ").strip()

print(f"\nAttempting connection to: {url} as {email}...")

try:
    # 2. INITIALIZE
    # cloud=True is strictly required for .atlassian.net
    jira = Jira(
        url=url,
        username=email,
        password=token,
        cloud=True 
    )

    # 3. TEST 1: Authentication (Who am I?)
    print("\nTest 1: Checking Authentication...")
    myself = jira.myself()
    print(f"✅ Auth Success! Logged in as: {myself['displayName']} (AccountId: {myself['accountId']})")

    # 4. TEST 2: Permissions (Can I see projects?)
    print("\nTest 2: Listing Projects...")
    projects = jira.projects()
    print(f"✅ Success! Found {len(projects)} projects.")
    
    # Print the first 3 projects found to verify
    for p in projects[:3]:
        print(f"   - {p['name']} (Key: {p['key']})")

    # 5. TEST 3: Specific Project 'KAN' (Edit this portion to be your project KEY)
    print("\nTest 3: Checking specific project 'KAN'...")
    try:
        project_kan = jira.project("KAN")
        print(f"✅ Project 'KAN' found directly! ID: {project_kan['id']}")
    except Exception as e:
        print(f"❌ Could not find project 'KAN'. Please check the Key spelling.")

except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print("-" * 30)
    print(f"Error Details: {e}")
    print("-" * 30)
    
    # Common Error Explanations
    error_str = str(e)
    if "401" in error_str:
        print("\nPossible Causes for 401 (Unauthorized):")
        print("1. The API Token is invalid. Did you generate it at https://id.atlassian.com/manage-profile/security/api-tokens ?")
        print("2. The Email does not match the account that created the token.")
        print("3. You are trying to use a password instead of an API Token.")
    elif "404" in error_str:
        print("\nPossible Causes for 404 (Not Found):")
        print("1. The URL is wrong. It must match 'https://something.atlassian.net'.")

        print("2. The user does not have permission to access this Jira instance.")
