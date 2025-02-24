import socket
import threading

# Используйте IP-адрес вашего сервера на DigitalOcean
HOST = '46.101.210.27'  # Замените на ваш публичный IP
PORT = 12345            # Порт сервера

def receive_messages(sock):
    """Получает и выводит сообщения от сервера"""
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            print(message)
        except:
            print("Отключено от сервера")
            sock.close()
            break

def start_client():
    """Запускает клиент и подключается к серверу"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        message = input()
        if message.lower() == "exit":
            break
        client.send(message.encode('utf-8'))

    client.close()

start_client()
