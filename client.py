import socket
import threading


HOST = '46.101.210.27'  
PORT = 12345           

def receive_messages(sock):
    
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            print(message)
        except:
            print("Від'єднано від сервера")
            sock.close()
            break

def start_client():
    
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
