import base64
import io
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image
import os
from tkinter import simpledialog


class MainWindow(CTk):
   def __init__(self):
       super().__init__()

       self.geometry('400x300')
       self.title("Chat Client")

       self.username = "new user"

       # Меню
       self.label = None
       self.menu_frame = CTkFrame(self, width=30, height=300)
       self.menu_frame.pack_propagate(False)
       self.menu_frame.place(x=0, y=0)
       self.is_show_menu = False
       self.speed_animate_menu = -20
       self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
       self.btn.place(x=0, y=0)

       # Основне поле чату
       self.chat_field = CTkScrollableFrame(self)
       self.chat_field.place(x=0, y=0)

       # Поле введення та кнопки
       self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
       self.message_entry.place(x=0, y=0)
       self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
       self.send_button.place(x=0, y=0)

       self.open_img_button = CTkButton(self, text='📂', width=50, height=40, command=self.open_image)
       self.open_img_button.place(x=0, y=0)

       self.adaptive_ui()

       try:
           self.sock = socket(AF_INET, SOCK_STREAM)
           self.sock.connect(('localhost', 8080))
           hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
           self.sock.send(hello.encode('utf-8'))
           threading.Thread(target=self.recv_message, daemon=True).start()
       except Exception as e:
           self.add_message(f"Не вдалося підключитися до сервера: {e}")

   def toggle_show_menu(self):
       if self.is_show_menu:
           self.is_show_menu = False
           self.speed_animate_menu *= -1
           self.btn.configure(text='▶️')
           self.show_menu()
       else:
           self.is_show_menu = True
           self.speed_animate_menu *= -1
           self.btn.configure(text='◀️')
           self.show_menu()
           # При відкритті меню – додамо приміром зміну імені
           self.label = CTkLabel(self.menu_frame, text='Імʼя')
           self.label.pack(pady=30)
           self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
           self.entry.pack()
           # Кнопка збереження
           self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
           self.save_button.pack()

   def show_menu(self):
       self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
       if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
           self.after(10, self.show_menu)
       elif self.menu_frame.winfo_width() >= 60 and not self.is_show_menu:
           self.after(10, self.show_menu)
           if self.label:
               self.label.destroy()
           if getattr(self, "entry", None):
               self.entry.destroy()
           if getattr(self, "save_button", None):
               self.save_button.destroy()

   def save_name(self):
       new_name = self.entry.get().strip()
       if new_name:
           self.username = new_name
           self.add_message(f"Ваш новий нік: {self.username}")

   def adaptive_ui(self):
       self.menu_frame.configure(height=self.winfo_height())
       self.chat_field.place(x=self.menu_frame.winfo_width())
       self.chat_field.configure(width=self.winfo_width() - self.menu_frame.winfo_width() - 20,
                                 height=self.winfo_height() - 40)
       self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
       self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.send_button.winfo_y())
       self.message_entry.configure(
           width=self.winfo_width() - self.menu_frame.winfo_width() - 110)
       self.open_img_button.place(x=self.winfo_width()-105, y=self.send_button.winfo_y())

       self.after(50, self.adaptive_ui)

   def add_message(self, message, img=None, is_own=False, message_id=None):
       message_frame = CTkFrame(self.chat_field, fg_color="grey")
       message_frame.pack(pady=5, anchor="w")

       wrapleng_size = max(
           100,
           self.winfo_width() - self.menu_frame.winfo_width() - 40
       )

       message_label = CTkLabel(
           message_frame,
           text=message,
           wraplength=wrapleng_size,
           text_color="white",
           justify="left"
       )
       message_label.pack(padx=10, pady=5)

       if img is not None:
           image_label = CTkLabel(
               message_frame,
               text="",
               image=img
           )
           image_label.pack(padx=10, pady=5)

       if not hasattr(self, "messages"):
           self.messages = {}

       if message_id is not None:
           self.messages[message_id] = {
               "frame": message_frame,
               "label": message_label,
               "text": message
           }

       if is_own and message_id is not None:
           edit_button = CTkButton(
               message_frame,
               text="✏️ Редагувати",
               width=120,
               height=28,
               command=lambda mid=message_id: self.edit_message(mid)
           )
           edit_button.pack(padx=5, pady=(0, 5), anchor="e")

   def send_message(self):
       message = self.message_entry.get().strip()

       if not message:
           return

       import uuid
       message_id = str(uuid.uuid4())

       self.add_message(
           f"{self.username}: {message}",
           is_own=True,
           message_id=message_id
       )

       data = f"TEXT@{self.username}@{message}\n"

       try:
           self.sock.sendall(data.encode("utf-8"))
       except Exception as e:
           self.add_message(f"Помилка відправки: {e}")

       self.message_entry.delete(0, END)

   def edit_message(self, message_id):
       message_data = self.messages.get(message_id)

       if not message_data:
           return

       old_text = message_data["text"]

       prefix = f"{self.username}: "
       editable_text = (
           old_text[len(prefix):]
           if old_text.startswith(prefix)
           else old_text
       )

       new_text = simpledialog.askstring(
           "Редагування повідомленя",
           "Заміни повідомленя:",
           initialvalue=editable_text,
           parent=self
       )

       if new_text is None:
           return

       new_text = new_text.strip()
       if not new_text:
           return

       updated_text = f"{self.username}: {new_text}"

       message_data["label"].configure(text=updated_text)
       message_data["text"] = updated_text

       try:
           self.sock.sendall(
               f"EDIT@{self.username}@{message_id}@{new_text}\n".encode("utf-8")
           )
       except Exception as e:
           self.add_message(f"Помилка надсилання зміни: {e}")

   def recv_message(self):
       buffer = ""
       while True:
           try:
               chunk = self.sock.recv(4096)
               if not chunk:
                   break
               buffer += chunk.decode('utf-8', errors='ignore')

               while "\n" in buffer:
                   line, buffer = buffer.split("\n", 1)
                   self.handle_line(line.strip())

           except:
               break
       self.sock.close()

   def handle_line(self, line):
       if not line:
           return
       parts = line.split("@", 3)
       msg_type = parts[0]

       if msg_type == "TEXT":
           if len(parts) >= 3:
               author = parts[1]
               message = parts[2]
               self.add_message(f"{author}: {message}")
       elif msg_type == "IMAGE":
           if len(parts) >= 4:
               author = parts[1]
               filename = parts[2]
               b64_img = parts[3]
               try:
                   img_data = base64.b64decode(b64_img)
                   pil_img = Image.open(io.BytesIO(img_data))
                   ctk_img = CTkImage(pil_img, size=(300, 300))
                   self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
               except Exception as e:
                   self.add_message(f"Помилка відображення зображення: {e}")
       else:
           self.add_message(line)

   def open_image(self):
       file_name = filedialog.askopenfilename()
       if not file_name:
           return
       try:
           with open(file_name, "rb") as f:
               raw = f.read()
           b64_data = base64.b64encode(raw).decode()
           short_name = os.path.basename(file_name)
           data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
           self.sock.sendall(data.encode())
           self.add_message('', CTkImage(light_image=Image.open(file_name), size=(300, 300)))
       except Exception as e:
           self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
   win = MainWindow()
   win.mainloop()