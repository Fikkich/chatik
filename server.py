import socket
import threading

# Настройки сервера
HOST = '127.0.0.1'  # Локальный хост
PORT = 12345        # Порт сервера

# Список подключенных клиентов
clients = []

def broadcast(message, sender_socket):
    """Отправляет сообщение всем клиентам, кроме отправителя"""
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                clients.remove(client)

def handle_client(client_socket):
    """Обрабатывает сообщения от клиента"""
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break
            broadcast(message, client_socket)
        except:
            break
    
    print("Клиент отключился")
    clients.remove(client_socket)
    client_socket.close()

def start_server():
    """Запускает сервер и принимает клиентов"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Сервер запущен на {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"Новое подключение: {client_address}")
        
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket,)).start()

# Запуск сервера
start_server()
