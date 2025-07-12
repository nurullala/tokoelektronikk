#!/usr/bin/env python3
"""
Aplikasi GUI Sederhana dengan Tkinter
"""

import tkinter as tk
from tkinter import messagebox
from src.utils import format_text, get_current_time

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Python Sederhana")
        self.root.geometry("400x300")
        self.root.configure(bg='#f0f0f0')
        
        # Membuat dan menempatkan widget
        self.create_widgets()
        
    def create_widgets(self):
        # Label judul
        title_label = tk.Label(
            self.root, 
            text="Selamat Datang di Aplikasi Python!", 
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=20)
        
        # Frame untuk input
        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(pady=10)
        
        # Label dan Entry untuk nama
        tk.Label(input_frame, text="Masukkan nama Anda:", bg='#f0f0f0').pack()
        self.name_entry = tk.Entry(input_frame, width=30, font=("Arial", 12))
        self.name_entry.pack(pady=5)
        
        # Button untuk menyapa
        greet_button = tk.Button(
            input_frame,
            text="Sapa Saya!",
            command=self.greet_user,
            bg='#4CAF50',
            fg='white',
            font=("Arial", 12),
            relief=tk.RAISED,
            cursor='hand2'
        )
        greet_button.pack(pady=10)
        
        # Button untuk menampilkan waktu
        time_button = tk.Button(
            input_frame,
            text="Tampilkan Waktu",
            command=self.show_time,
            bg='#2196F3',
            fg='white',
            font=("Arial", 12),
            relief=tk.RAISED,
            cursor='hand2'
        )
        time_button.pack(pady=5)
        
        # Button untuk keluar
        exit_button = tk.Button(
            input_frame,
            text="Keluar",
            command=self.root.quit,
            bg='#f44336',
            fg='white',
            font=("Arial", 12),
            relief=tk.RAISED,
            cursor='hand2'
        )
        exit_button.pack(pady=10)
        
        # Label untuk menampilkan hasil
        self.result_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            bg='#f0f0f0',
            fg='#333333',
            wraplength=350
        )
        self.result_label.pack(pady=20)
        
    def greet_user(self):
        """Fungsi untuk menyapa pengguna"""
        name = self.name_entry.get().strip()
        if name:
            formatted_name = format_text(name)
            message = f"Halo {formatted_name}! Senang bertemu dengan Anda!"
            self.result_label.config(text=message)
        else:
            messagebox.showwarning("Peringatan", "Silakan masukkan nama Anda terlebih dahulu!")
            
    def show_time(self):
        """Fungsi untuk menampilkan waktu saat ini"""
        current_time = get_current_time()
        self.result_label.config(text=f"Waktu saat ini: {current_time}")

def main():
    """Fungsi utama untuk menjalankan aplikasi GUI"""
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 