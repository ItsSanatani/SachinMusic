import os

session_name = "Chatbot"  # यहाँ अपने session का नाम डालो (फाइल का नाम बिना `.session` extension)

# Delete old session files
extensions = [".session", ".session-journal", ".session-shm", ".session-wal"]

deleted = False
for ext in extensions:
    file = session_name + ext
    if os.path.exists(file):
        os.remove(file)
        print(f"Deleted: {file}")
        deleted = True

if not deleted:
    print("No session files found.")
else:
    print("Old session deleted successfully.")
