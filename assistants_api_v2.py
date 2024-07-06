import time
from openai import OpenAI

OPENAI_API_KEY="ENTER_YOUR_API_KEY_HERE"
client = OpenAI(api_key=OPENAI_API_KEY)

def createAssistant(file_ids, title):
    instructions = """
    You are a helpful assistant. Use your knowledge base to answer user questions.
    """
    model = "gpt-3.5-turbo-0125" # gpt-4o | gpt-4-turbo | gpt-3.5-turbo-0125
    tools = [{"type": "file_search"}]
    vector_store = client.beta.vector_stores.create(name=title, file_ids=file_ids)
    tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}}
    assistant = client.beta.assistants.create(
        name=title,
        instructions=instructions,
        model=model,
        tools=tools,
        tool_resources=tool_resources
    )
    return assistant.id, vector_store.id

def saveFileOpenAI(location):
    file = client.files.create(file=open(location, "rb"), purpose='assistants')
    # os.remove(location)
    return file.id

def startAssistantThread(prompt, vector_id):
    messages = [{"role": "user", "content": prompt}]
    tool_resources = {"file_search": {"vector_store_ids": [vector_id]}}
    thread = client.beta.threads.create(messages=messages, tool_resources=tool_resources)
    return thread.id

def runAssistant(thread_id, assistant_id):
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)
    return run.id

def checkRunStatus(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run.status

def retrieveThread(thread_id):
    thread_messages = client.beta.threads.messages.list(thread_id)
    list_messages = thread_messages.data
    thread_messages = []
    for message in list_messages:
        obj = {}
        obj['content'] = message.content[0].text.value
        obj['role'] = message.role
        thread_messages.append(obj)
    return thread_messages[::-1]

def addMessageToThread(thread_id, prompt):
    thread_message = client.beta.threads.messages.create(thread_id, role="user", content=prompt)

# Example
file_location = "secretcode.txt"
assistant_title = "MyAssistant"

file_id = saveFileOpenAI(file_location)
print(f"\nFile ID: {file_id}")

assistant_id, vector_store_id = createAssistant([file_id], assistant_title)
print(f"\nAssistant ID: {assistant_id}, Vector Store ID: {vector_store_id}")

# Send message
prompt = "Provide me with only the secret code from our file."
thread_id = startAssistantThread(prompt, vector_store_id)
print(f"\nThread ID: {thread_id}")

run_id = runAssistant(thread_id, assistant_id)
print(f"\nRun ID: {run_id}")

status = checkRunStatus(thread_id, run_id)
while status == "in_progress" or status == "queued":
    time.sleep(1)
    status = checkRunStatus(thread_id, run_id)
print(f"\nRun Status: {status}")

messages = retrieveThread(thread_id)
print("\nThread Messages:")
for message in messages:
    print(f"{message['role']}: {message['content']}")

# Send message
new_prompt = "Can you provide more details about this code from the file?"
addMessageToThread(thread_id, new_prompt)

run_id = runAssistant(thread_id, assistant_id)
print(f"\nRun ID: {run_id}")

status = checkRunStatus(thread_id, run_id)
while status == "in_progress" or status == "queued":
    time.sleep(1)
    status = checkRunStatus(thread_id, run_id)
print(f"\nRun Status: {status}")

updated_messages = retrieveThread(thread_id)
print("\nUpdated Thread Messages:")
for message in updated_messages:
    print(f"{message['role']}: {message['content']}")

response = client.beta.assistants.delete(assistant_id)
print("\nDELETED THIS ASSISTANT:", response, "\n")