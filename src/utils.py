"""
Modul utilitas untuk aplikasi Python
"""

def format_text(text):
    """Memformat teks dengan kapitalisasi yang benar"""
    return text.title()

def calculate_sum(numbers):
    """Menghitung jumlah dari list angka"""
    return sum(numbers)

def is_even(number):
    """Mengecek apakah angka genap"""
    return number % 2 == 0

def get_current_time():
    """Mendapatkan waktu saat ini"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 