"""
ChromeDriver Setup and Fix Utility
Downloads and configures ChromeDriver automatically
"""
import os
import sys
import subprocess
import platform
import requests
import zipfile

def get_chrome_version():
    """Detect installed Chrome version"""
    try:
        if platform.system() == "Windows":
            # Try registry method first
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                return version
            except:
                pass
            
            # Try command line
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    try:
                        result = subprocess.run([path, "--version"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            import re
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                            if match:
                                return match.group(1)
                    except:
                        continue
        
        elif platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    import re
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
            except:
                pass
        
        else:  # Linux
            try:
                result = subprocess.run(["google-chrome", "--version"],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    import re
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
            except:
                pass
        
        return None
        
    except Exception as e:
        print(f"Error detecting Chrome version: {e}")
        return None

def download_chromedriver(version=None):
    """Download compatible ChromeDriver"""
    try:
        print("🔄 Downloading ChromeDriver...")
        
        # Determine platform
        system = platform.system().lower()
        if system == "windows":
            platform_suffix = "win32"
            driver_name = "chromedriver.exe"
        elif system == "darwin":
            platform_suffix = "mac64"
            driver_name = "chromedriver"
        else:
            platform_suffix = "linux64"
            driver_name = "chromedriver"
        
        # Get ChromeDriver version
        if version:
            major_version = version.split('.')[0]
            try:
                response = requests.get(
                    f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}",
                    timeout=10
                )
                if response.status_code == 200:
                    chromedriver_version = response.text.strip()
                else:
                    raise Exception("Version not found")
            except:
                print(f"Could not find ChromeDriver for Chrome {major_version}, using latest")
                response = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
                chromedriver_version = response.text.strip()
        else:
            response = requests.get("https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
            chromedriver_version = response.text.strip()
        
        # Download URL
        download_url = (f"https://chromedriver.storage.googleapis.com/"
                       f"{chromedriver_version}/chromedriver_{platform_suffix}.zip")
        
        print(f"   📦 Version: {chromedriver_version}")
        print(f"   🌐 Downloading from: {download_url}")
        
        # Download
        response = requests.get(download_url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Download failed: HTTP {response.status_code}")
        
        # Save and extract
        zip_path = "chromedriver.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        
        # Make executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(driver_name, 0o755)
        
        if os.path.exists(driver_name):
            print(f"   ✅ ChromeDriver saved: {driver_name}")
            return True
        else:
            raise Exception("ChromeDriver file not created")
        
    except Exception as e:
        print(f"   ❌ ChromeDriver download failed: {e}")
        return False

def fix_chromedriver():
    """Main ChromeDriver fix function"""
    print("🔧 CHROMEDRIVER SETUP & FIX")
    print("=" * 50)
    
    # Check Chrome installation
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"✅ Chrome detected: {chrome_version}")
    else:
        print("❌ Google Chrome not detected")
        print("   Please install Google Chrome first")
        return False
    
    # Check existing ChromeDriver
    driver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    
    if os.path.exists(driver_name):
        print(f"📁 Existing ChromeDriver found: {driver_name}")
        choice = input("Replace with latest version? (y/n): ").lower()
        if choice != 'y':
            return True
        
        try:
            os.remove(driver_name)
        except:
            pass
    
    # Download ChromeDriver
    if download_chromedriver(chrome_version):
        print("🎉 ChromeDriver setup completed successfully!")
        return True
    
    print("❌ ChromeDriver setup failed")
    return False

def main():
    """Main function"""
    print("Google Meet Bot - ChromeDriver Setup")
    print("=" * 60)
    
    success = fix_chromedriver()
    
    if success:
        print("\n🎉 Setup completed! You can now run the bot.")
    else:
        print("\n❌ Setup failed. Please resolve issues manually.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
