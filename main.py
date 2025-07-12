#!/usr/bin/env python3
"""
Aplikasi Python - Entry Point
"""

def console_app():
    """Aplikasi console sederhana"""
    print("=" * 50)
    print("Selamat datang di aplikasi Python Console!")
    print("=" * 50)
    
    # Import fungsi dari utils
    from src.utils import format_text, calculate_sum, is_even, get_current_time
    
    # Demo fungsi-fungsi
    print(f"Waktu saat ini: {get_current_time()}")
    
    # Input dari user
    name = input("Masukkan nama Anda: ")
    if name:
        print(f"Halo {format_text(name)}!")
    
    # Demo perhitungan
    numbers = [1, 2, 3, 4, 5]
    print(f"Jumlah dari {numbers}: {calculate_sum(numbers)}")
    
    # Demo pengecekan angka genap
    num = int(input("Masukkan angka untuk dicek (genap/ganjil): "))
    result = "genap" if is_even(num) else "ganjil"
    print(f"Angka {num} adalah {result}")
    
    print("\nTerima kasih telah menggunakan aplikasi!")

def web_app():
    """Menjalankan aplikasi web Flask"""
    try:
        import app_web
        print("🚀 Menjalankan aplikasi web...")
        print("📱 Buka browser dan kunjungi: http://localhost:5000")
        print("⏹️  Tekan Ctrl+C untuk menghentikan server")
        app_web.app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("💡 Pastikan Flask sudah terinstall dengan menjalankan:")
        print("   pip install flask")
    except Exception as e:
        print(f"❌ Error menjalankan aplikasi web: {e}")

def main():
    """Fungsi utama aplikasi"""
    print("Pilih jenis aplikasi yang ingin dijalankan:")
    print("1. Aplikasi Console")
    print("2. Aplikasi GUI (Tkinter)")
    print("3. Aplikasi Web (Flask)")
    print("4. Keluar")
    
    while True:
        choice = input("\nMasukkan pilihan (1-4): ").strip()
        
        if choice == "1":
            console_app()
            break
        elif choice == "2":
            try:
                import app_gui
                app_gui.main()
            except ImportError as e:
                print(f"Error: {e}")
                print("Pastikan file app_gui.py ada di folder yang sama")
            break
        elif choice == "3":
            web_app()
            break
        elif choice == "4":
            print("Terima kasih! Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid. Silakan pilih 1, 2, 3, atau 4.")
    
if __name__ == "__main__":
    main() 