import tkinter as tk
from tkinter import messagebox

def on_button_click():
    user_input = entry.get()
    if user_input:
        label_output.config(text=f"Вы ввели: {user_input}")
    else:
        messagebox.showwarning("Предупреждение", "Введите текст!")

# Создание главного окна
root = tk.Tk()
root.title("Простое GUI приложение")
root.geometry("300x200")

# Поле ввода
entry = tk.Entry(root)
entry.pack(pady=10)

# Кнопка
button = tk.Button(root, text="Показать", command=on_button_click)
button.pack()

# Метка для вывода текста
label_output = tk.Label(root, text="")
label_output.pack(pady=10)

# Запуск приложения
root.mainloop()
