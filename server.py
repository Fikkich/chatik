import socket
import threading
import json
import hashlib
import os
from datetime import datetime

HOST = '0.0.0.0'
PORT = 12345

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")
LOG_FILE = os.path.join(BASE_DIR, "server_log.json")

clients = []
client_user_map = {}

END_TAG = "|END"

def send_msg(sock, msg: str):
    if not msg.endswith(END_TAG):
        msg += END_TAG
    sock.sendall(msg.encode('utf-8'))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def disconnect_client(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)
    if client_socket in client_user_map:
        del client_user_map[client_socket]
    client_socket.close()

def load_users_from_db():
    users = {}
    try:
        with open(DB_FILE, "r") as db_file:
            for line in db_file:
                data = json.loads(line.strip())
                users[data["Login"]] = data
    except FileNotFoundError:
        pass
    return users

def save_user_to_db(user_data):
    users = load_users_from_db()
    users[user_data["Login"]] = user_data
    with open(DB_FILE, "w") as db_file:
        for user in users.values():
            db_file.write(json.dumps(user) + "\n")

def broadcast(message, sender_socket):
    sender_login = client_user_map.get(sender_socket, "Unknown")
    for client in clients:
        if client != sender_socket:
            try:
                send_msg(client, message)
            except:
                client.close()
                clients.remove(client)

def save_user_chats_on_disconnect(login):
    if login in users_db:
        user_data = users_db[login]
        save_user_to_db(user_data)

def send_private_message(message, sender_socket, recipient_login):
    sender_login = client_user_map.get(sender_socket, "Unknown")
    recipient_socket = None

    if isinstance(message, bytes):
        message = message.decode('utf-8')

    for sock, login in client_user_map.items():
        if login == recipient_login:
            recipient_socket = sock
            break

    if recipient_socket:
        try:
            formatted_message = f"INCOMEMSG|{sender_login}|{message}"
            send_msg(recipient_socket, formatted_message)
        except Exception as e:
            recipient_socket.close()
    else:
        if recipient_login in users_db:
            recipient_data = users_db[recipient_login]
            sender_data = users_db.get(sender_login, None)

            if not sender_data:
                send_msg(sender_socket, f"Error: Відправник {sender_login} не знайдений у базі")
                return

            msg_data = {
                "message": str(message).replace('\\', '\\\\').replace('"', '\\"'),
                "imageBytes": None,
                "isReaded": False,
                "isUserMessage": False
            }

            recipient_chat = next((chat for chat in recipient_data["Chats"] if chat["userChatName"] == sender_login), None)
            if recipient_chat is None:
                recipient_chat = {"userChatName": sender_login, "messages": []}
                recipient_data["Chats"].append(recipient_chat)

            recipient_chat["messages"].append(msg_data)
            save_user_to_db(recipient_data)
        else:
            send_msg(sender_socket, f"Error: Користувач {recipient_login} не знайдений у базі")

def send_private_image(image_bytes_base64, sender_socket, recipient_login):
    sender_login = client_user_map.get(sender_socket, "Unknown")
    recipient_socket = None

    for sock, login in client_user_map.items():
        if login == recipient_login:
            recipient_socket = sock
            break

    if recipient_socket:
        try:
            formatted_message = f"INCOMEIMG|{sender_login}|{image_bytes_base64}"
            send_msg(recipient_socket, formatted_message)
        except Exception as e:
            print(f"Error while sending image to {recipient_login}: {e}")
            recipient_socket.close()
    else:
        # Обробка offline користувача
        if recipient_login in users_db:
            recipient_data = users_db[recipient_login]
            sender_data = users_db.get(sender_login, None)

            if not sender_data:
                send_msg(sender_socket, f"Error: Відправник {sender_login} не знайдений у базі")
                return

            # Формуємо структуру повідомлення для збереження
            msg_data = {
                "message": None,
                "imageBytes": image_bytes_base64,
                "messageType": 1,
                "isReaded": False,
                "isUserMessage": False
            }

            # Знаходимо або створюємо чат
            recipient_chat = next((chat for chat in recipient_data["Chats"] if chat["userChatName"] == sender_login), None)
            if recipient_chat is None:
                recipient_chat = {"userChatName": sender_login, "messages": []}
                recipient_data["Chats"].append(recipient_chat)

            recipient_chat["messages"].append(msg_data)
            save_user_to_db(recipient_data)

            print(f"Фото збережено в чат {recipient_login} ⇐ {sender_login} (offline)")
        else:
            send_msg(sender_socket, f"Error: Користувач {recipient_login} не знайдений у базі")


def notify_friends_about_status_change(login, is_online):
    user_data = users_db.get(login, {})
    if not user_data:
        return

    for sock, other_login in client_user_map.items():
        if other_login == login:
            continue

        other_user_data = users_db.get(other_login, {})
        if not other_user_data:
            continue

        # Якщо у цього користувача є чат з login — надсилаємо йому оновлення
        if any(chat["userChatName"] == login for chat in other_user_data.get("Chats", [])):
            try:
                status_msg = f'STATUSUPDATE|{login}|{"online" if is_online else "offline"}'
                send_msg(sock, status_msg)
            except Exception as e:
                print(f"Не вдалося повідомити {other_login} про статус {login}: {e}")

def handle_client(client_socket):
    login = None
    buffer = ""
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            buffer += data

            while END_TAG in buffer:
                message, buffer = buffer.split(END_TAG, 1)
                print(f"Отримано повідомлення від клієнта: {message}")
                parts = message.split('|')

                if parts[0] == "1":
                    login = parts[1]
                    password = parts[2]
                    if login in users_db:
                        send_msg(client_socket, "Error: Користувач з таким логіном вже існує")
                    else:
                        users_db[login] = {
                        "Login": login,
                        "Password": hash_password(password),
                         "Chats": []
                        }
                        save_user_to_db(users_db[login])
        
                        client_user_map[client_socket] = login
        
                        send_msg(client_socket, "Реєстрація успішна")
                        send_msg(client_socket, 'CHATS|[]')

                elif parts[0] == "2":
                    login = parts[1]
                    password = parts[2]
                    if login in users_db and users_db[login]["Password"] == hash_password(password):
                        client_user_map[client_socket] = login
                        send_msg(client_socket, "Авторизація успішна")
                        send_msg(client_socket, f'CHATS|{json.dumps(users_db[login]["Chats"])}')

                     # 🔥 Надсилання списку онлайн друзів
                    user_chats = users_db[login]["Chats"]
                    online_friends = []
                    for chat in user_chats:
                        friend = chat["userChatName"]
                        if friend in client_user_map.values() and friend != login:
                            online_friends.append(friend)

                        send_msg(client_socket, f'FRIENDSONLINE|{json.dumps(online_friends)}')

                        # 🔔 Повідомити друзів, що користувач зайшов онлайн
                        notify_friends_about_status_change(login, True)
                    else:
                        send_msg(client_socket, "Error: Невірний логін або пароль")

                elif parts[0] == "3":
                    login = client_user_map.get(client_socket)
                    if login:
                        users_db[login]["Chats"] = json.loads(parts[1])
                        save_user_to_db(users_db[login])

                elif parts[0] == "4":
                    login_list = list(users_db.keys())
                    send_msg(client_socket, f'USERS|{json.dumps({"items": login_list})}')

                elif parts[0] == "5":
                    recipient_login = parts[1]
                    chat_message = '|'.join(parts[2:])
                    send_private_message(chat_message, client_socket, recipient_login)

                elif parts[0] == "6":
                    recipient_login = parts[1]
                    image_base64 = parts[2]
                    send_private_image(image_base64, client_socket, recipient_login)

                elif parts[0] == "7":
                    login = client_user_map.get(client_socket)
                    if login:
                        user_chats = users_db[login]["Chats"]
                        online_friends = []
                        for chat in user_chats:
                            friend = chat["userChatName"]
                            if friend in client_user_map.values() and friend != login:
                                online_friends.append(friend)

                                send_msg(client_socket, f'FRIENDSONLINE|{json.dumps(online_friends)}')
                            else:
                                send_msg(client_socket, "Error: Користувач не авторизований")
                else:
                    broadcast(message.encode('utf-8'), client_socket)

    except Exception as e:
        print(f"Помилка при обробці клієнта: {e}")
    finally:
        if login:
            save_user_chats_on_disconnect(login)
            notify_friends_about_status_change(login, False)  # ⬅️ повідомлення про вихід
        print("Клієнт відключився")
        disconnect_client(client_socket)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Сервер успішно запущений {HOST}:{PORT}")

    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"Нове підключення: {client_address}")
            clients.append(client_socket)
            threading.Thread(target=handle_client, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("Остановка сервера...")
        save_all_users_to_db()
        server.close()

def save_all_users_to_db():
    for login in users_db.keys():
        save_user_chats_on_disconnect(login)
    print("Все дані збережено.")

users_db = load_users_from_db()
start_server()
