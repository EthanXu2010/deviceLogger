import os
import json
from cryptography.fernet import Fernet
import base64


SECRET_KEY = b'y0X9MV0VZqxTiGlRQfSpbFzUEvPyW69PMH9Xz1Tn1E0='  


fernet = Fernet(SECRET_KEY)

def decrypt_content(encrypted_content):
    """Decrypt content using the SECRET_KEY."""
    decrypted_data = fernet.decrypt(encrypted_content.encode('utf-8'))
    return decrypted_data

def find_session_esecure_file():
    """Search for the session.esecure file in the same directory."""
    current_dir = os.getcwd()
    session_file = os.path.join(current_dir, 'session.esecure')

    if os.path.exists(session_file):
        print(f"Found session.esecure at: {session_file}")
        return session_file
    else:
        print("session.esecure file not found in the current directory.")
        return None

def validate_password_one(password_one):
    """Validate the first password and derive the second password."""
    PREFIX_ONE = "2010"
    SUFFIX_ONE = "0130"
    
    if password_one.startswith(PREFIX_ONE) and password_one.endswith(SUFFIX_ONE):
        
        middle_part = password_one[len(PREFIX_ONE):-len(SUFFIX_ONE)]
        
        password_two = base64.b64encode(middle_part.encode()).decode()
        print("Now enter password two.")  
        return password_two
    else:
        print("Password one is incorrect.")
        return None

def decrypt_esecure_file(esecure_file):
    """Decrypt an .esecure file and extract its contents."""
    
    with open(esecure_file, 'r') as file:
        esecure_data = json.load(file)

    
    password_one = input("Enter password one: ")
    password_two = validate_password_one(password_one)

    if not password_two:
        print("Password one is incorrect.")
        return

    entered_password_two = input("Enter password two: ")

    if entered_password_two != password_two:
        print("Password two is incorrect. Opening dummy file...")
        open_dummy_file()
        return

    
    for item in esecure_data:
        file_name = item['name']
        encrypted_content = item['content']

        try:
            decrypted_content = decrypt_content(encrypted_content)
            
            
            mode = 'wb' if file_name.endswith(('.mp4', '.jpg', '.png')) else 'w'
            with open(f'decrypted_{file_name}', mode) as f:
                f.write(decrypted_content if mode == 'wb' else decrypted_content.decode('utf-8'))

            print(f"Decrypted content saved to decrypted_{file_name}.")
        
        except Exception as e:
            print(f"Failed to decrypt {file_name}: {e}")

def open_dummy_file():
    """Open a dummy file with a message."""
    with open('bucketlist.txt', 'w') as f:
        f.write("Bucket List: \n1. Skydiving\n2. Visit the Moon\n3. Write a Bestseller\n4. Learn Python like a pro!\n")
    print("Dummy file 'bucketlist.txt' opened instead.")

def main():
    
    session_file = find_session_esecure_file()

    if not session_file:
        print("No session.esecure file found in the current directory.")
        return

    
    decrypt_esecure_file(session_file)

if __name__ == "__main__":
    main()
