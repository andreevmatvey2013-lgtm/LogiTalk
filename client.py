from socket import *
import threading

HOST = '7.tcp.eu.ngrok.io'
PORT = 19992

client_socket = socket(AF_INET, SOCK_STREAM)
name = input("Введіть ім'я: ")
client_socket.connect((HOST, PORT))
client_socket.send(name.encode())

def send_message():
   while True:
       client_message = input()
       if client_message.lower() == 'exit':
           client_socket.close()
           break
       client_socket.send(client_message.encode())


threading.Thread(target=send_message).start() # запуск потока відправки повідомлень
while True:
   try:
       message = client_socket.recv(1024).decode().strip()
       if message:
           print(message)
   except:
       break