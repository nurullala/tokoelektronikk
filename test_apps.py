#!/usr/bin/env python3
"""
Test script untuk memverifikasi aplikasi web
"""

import subprocess
import time
import requests
import sys

def test_app(app_name, port=5000):
    """Test aplikasi web"""
    print(f"🧪 Testing {app_name}...")
    
    try:
        # Start the app
        process = subprocess.Popen([sys.executable, app_name], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for app to start
        time.sleep(3)
        
        # Test if app responds
        try:
            response = requests.get(f'http://localhost:{port}', timeout=5)
            if response.status_code == 200:
                print(f"✅ {app_name} berjalan dengan baik!")
                return True
            else:
                print(f"❌ {app_name} merespons dengan status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {app_name} tidak dapat diakses: {e}")
            return False
        finally:
            # Kill the process
            process.terminate()
            process.wait()
            
    except Exception as e:
        print(f"❌ Error testing {app_name}: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Memulai test aplikasi web...")
    print("=" * 50)
    
    # Test simple app
    success1 = test_app('app_web_simple.py', 5000)
    
    # Test MongoDB app
    success2 = test_app('app_web_mongodb.py', 5001)
    
    # Test main app
    success3 = test_app('app_web.py', 5002)
    
    print("=" * 50)
    print("📊 Hasil Test:")
    print(f"app_web_simple.py: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"app_web_mongodb.py: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"app_web.py: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if all([success1, success2, success3]):
        print("🎉 Semua aplikasi berjalan dengan baik!")
    else:
        print("⚠️  Beberapa aplikasi memiliki masalah")

if __name__ == '__main__':
    main() 