import os
import time
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException, WebDriverException
from selenium.webdriver.chrome.service import Service

class GoogleMeetBot:
    def __init__(self):
        self.browser = None
        self.is_active = False
        self.participant_names = []

    def setup_browser(self):
        options = Options()
        
        # ALLOW Chrome to ACCESS audio but keep bot INVISIBLE with mic indicator
        options.add_argument("--use-fake-ui-for-media-stream")      # Auto-approve media
        options.add_argument("--allow-running-insecure-content")    # Allow insecure content
        options.add_argument("--disable-web-security")              # Disable web security
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        # DON'T mute audio - Chrome needs to hear meeting for recording
        # options.add_argument("--mute-audio")  # REMOVED
        
        # Stability & Performance
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # ALLOW Chrome audio access, BLOCK bot mic, show mic indicator
        prefs = {
            "profile.default_content_setting_values": {
                "media_stream": 1,              # ALLOW media streams for system recording
                "media_stream_mic": 1,          # ALLOW mic indicator (green circle) 
                "media_stream_camera": 2,       # BLOCK camera (bot invisible)
                "notifications": 2,             # BLOCK notifications
                "geolocation": 2,               # BLOCK location
            },
            "profile.managed_default_content_settings": {
                "media_stream": 1               # ALLOW managed media for recording
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        # Unique temporary profile to avoid conflicts
        temp_profile_dir = os.path.join(os.getcwd(), f"temp_chrome_profile_{uuid.uuid4().hex[:8]}")
        options.add_argument(f"--user-data-dir={temp_profile_dir}")
        options.add_argument("--profile-directory=Default")

        try:
            print("Trying system ChromeDriver...")
            self.browser = webdriver.Chrome(options=options)
            print("✅ Using system ChromeDriver")
        except Exception as e:
            print(f"System ChromeDriver failed: {e}")
            try:
                if os.path.exists("chromedriver.exe"):
                    print("Trying local chromedriver.exe...")
                    service = Service("chromedriver.exe")
                    self.browser = webdriver.Chrome(service=service, options=options)
                    print("✅ Using local chromedriver.exe")
                else:
                    return False
            except Exception as e:
                print(f"Local ChromeDriver failed: {e}")
                return False

        # Anti-detection script
        self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return True

    def inject_invisibility_script(self):
        """Make bot invisible but KEEP microphone indicator (green circle) visible"""
        invisibility_script = """
        // BLOCK bot's actual microphone audio but KEEP visual indicator
        const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
        navigator.mediaDevices.getUserMedia = function(constraints) {
            if (constraints && constraints.audio) {
                // Create a silent audio stream to show mic indicator without actual audio
                return navigator.mediaDevices.getUserMedia({audio: false}).then(() => {
                    // Return a fake silent audio stream that shows indicator
                    const audioContext = new AudioContext();
                    const stream = audioContext.createMediaStreamDestination().stream;
                    return stream;
                }).catch(() => {
                    // Fallback: block actual mic but allow indicator
                    return Promise.reject(new Error('Microphone blocked for invisible bot'));
                });
            }
            return originalGetUserMedia.apply(this, arguments);
        };
        
        // Hide ONLY camera indicators, KEEP microphone indicator visible
        function hideCameraKeepMic() {
            const cameraSelectors = [
                'div[aria-label*="camera" i]:not([aria-label*="microphone" i])',
                '.camera-indicator:not(.mic-indicator)', 
                '[data-testid*="camera"]:not([data-testid*="mic"])',
                'button[aria-label*="camera" i]:not([aria-label*="microphone" i])'
            ];
            
            cameraSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    if (el.textContent.toLowerCase().includes('camera') ||
                        el.getAttribute('aria-label')?.toLowerCase().includes('camera')) {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                    }
                });
            });
            
            // EXPLICITLY keep microphone indicators visible for green circle
            const micSelectors = [
                'div[aria-label*="microphone" i]',
                '.mic-indicator',
                '[data-testid*="mic"]',
                'button[aria-label*="microphone" i]',
                '.recording-indicator'
            ];
            
            micSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                });
            });
        }
        
        hideCameraKeepMic();
        setInterval(hideCameraKeepMic, 1000);
        
        console.log('🚫 Bot silent, camera hidden, MIC INDICATOR VISIBLE');
        """
        
        try:
            self.browser.execute_script(invisibility_script)
            print("🚫 Invisibility script injected (mic indicator kept visible)")
        except Exception as e:
            print(f"⚠️ Script injection warning: {e}")

    def navigate_to_meet(self, url):
        try:
            # CRITICAL FIX: Add https:// if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            print(f"📱 Opening: {url}")
            self.browser.get(url)
            time.sleep(5)
            
            self.inject_invisibility_script()
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Failed to open URL: {e}")
            return False

    def force_complete_silence(self):
        """Keep bot silent but maintain microphone indicator visibility"""
        print("🚫 FORCING BOT SILENCE (keeping mic indicator visible)...")
        
        self.inject_invisibility_script()
        
        # Disable only bot's audio output, keep visual indicators
        silence_script = """
        // Disable bot's actual audio but keep visual indicators
        const botMediaElements = document.querySelectorAll('video[autoplay], audio[autoplay]');
        botMediaElements.forEach(el => {
            el.muted = true;
            el.pause();
        });
        
        // Hide only camera buttons, keep microphone visual indicators
        const cameraButtons = document.querySelectorAll('button[aria-label*="camera" i]:not([aria-label*="microphone" i])');
        cameraButtons.forEach(btn => {
            btn.style.display = 'none';
            btn.disabled = true;
        });
        
        // EXPLICITLY keep microphone buttons/indicators visible for green circle
        const micButtons = document.querySelectorAll('button[aria-label*="microphone" i]');
        micButtons.forEach(btn => {
            btn.style.display = 'block';
            btn.style.visibility = 'visible';
        });
        
        console.log('🚫 Bot silenced, mic indicator visible for green circle');
        """
        
        try:
            self.browser.execute_script(silence_script)
            print("   ✅ Bot silenced, mic indicator kept visible")
        except Exception as e:
            print(f"   ⚠️ Silence enforcement warning: {e}")

    def extract_real_participants(self):
        """Extract participant names with smart detection"""
        try:
            print("👥 Extracting REAL participant names...")
            participants = []
            
            # Try to open participant panel
            panel_opened = False
            show_selectors = [
                'button[aria-label^="Show people"]',
                'button[aria-label*="participant" i]', 
                'button[aria-label*="people" i]',
                '[data-testid="participants-button"]',
                'button[aria-label="Show everyone"]'
            ]
            
            for selector in show_selectors:
                try:
                    btn = WebDriverWait(self.browser, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    btn.click()
                    time.sleep(3)
                    panel_opened = True
                    print("   ✅ Participants panel opened")
                    break
                except:
                    continue
            
            if panel_opened:
                # Count total participants
                participant_count_elements = self.browser.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
                actual_count = len([elem for elem in participant_count_elements if elem.text.strip()])
                print(f"   📊 Detected {actual_count} participants in meeting")
                
                # Extract names from participant list
                name_selectors = [
                    'div[role="listitem"] .zWfAib',
                    'div[role="listitem"] .ZjFb7c',
                    'div[role="listitem"] span[jsname]',
                    '[data-participant-name]',
                    'div[role="listitem"] div[data-self-name]',
                    'div[role="listitem"] .participant-name'
                ]
                
                excluded_keywords = ['bot', 'recorder', 'recording', 'system', 'unknown', 'guest', 'you', '(you)', 'yourself']
                
                for selector in name_selectors:
                    try:
                        elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            name = elem.text.strip()
                            if (name and 
                                len(name) > 1 and 
                                len(name) < 50 and
                                not any(keyword in name.lower() for keyword in excluded_keywords) and
                                name not in participants):
                                participants.append(name)
                                print(f"   ✅ Found participant: {name}")
                        
                        if participants:
                            break
                    except:
                        continue
                
                # Close panel
                try:
                    close_selectors = ['button[aria-label="Close"]', 'button[aria-label*="close" i]']
                    for selector in close_selectors:
                        try:
                            close_btn = self.browser.find_element(By.CSS_SELECTOR, selector)
                            close_btn.click()
                            break
                        except:
                            continue
                except:
                    pass
                
                # Smart fallback with correct participant count
                unique_participants = list(dict.fromkeys(participants))
                
                if len(unique_participants) > 0:
                    if len(unique_participants) < actual_count:
                        # Add generic names for missing participants
                        fallback_names = ["Person 1", "Person 2", "Person 3", "Person 4", "Person 5"]
                        for name in fallback_names:
                            if name not in unique_participants:
                                unique_participants.append(name)
                            if len(unique_participants) >= actual_count:
                                break
                    
                    final_participants = unique_participants[:actual_count]
                    print(f"   🎯 Final participants: {', '.join(final_participants)}")
                    return final_participants
                else:
                    # No names found, use generic based on count
                    if actual_count >= 2:
                        generic_names = [f"Person {i+1}" for i in range(actual_count)]
                        print(f"   🔄 Using generic names for {actual_count} people: {', '.join(generic_names)}")
                        return generic_names
                    else:
                        print("   ⚠️ Using default 2-person setup")
                        return ["Person 1", "Person 2"]
            
            # Fallback if panel couldn't be opened
            print("   ⚠️ Couldn't open participant panel, using defaults")
            return ["Person 1", "Person 2"]
            
        except Exception as e:
            print(f"   ❌ Participant extraction error: {e}")
            return ["Person 1", "Person 2"]

    def mute_bot_audio(self):
        """Mute only bot's audio output, keep mic indicator visible"""
        try:
            mute_script = """
            // Mute only bot's audio elements, don't interfere with mic indicator
            const botAudioElements = document.querySelectorAll('audio[autoplay], video[autoplay]');
            botAudioElements.forEach(element => {
                element.muted = true;
                element.volume = 0;
            });
            
            // Keep microphone indicators visible
            const micIndicators = document.querySelectorAll('div[aria-label*="microphone" i]');
            micIndicators.forEach(indicator => {
                indicator.style.display = 'block';
                indicator.style.visibility = 'visible';
            });
            
            console.log('🔇 Bot audio muted, mic indicator visible for green circle');
            """
            
            self.browser.execute_script(mute_script)
            print("🔇 Bot audio muted (mic indicator visible for green circle)")
            
        except Exception as e:
            print(f"⚠️ Mute audio warning: {e}")

    def click_join(self):
        """Enhanced join button clicking"""
        print("🔍 Looking for join button...")
        
        join_methods = [
            ("XPATH", "//span[contains(text(), 'Join now')]", "Join now text"),
            ("XPATH", "//span[contains(text(), 'Ask to join')]", "Ask to join text"),
            ("XPATH", "//button[contains(text(), 'Join')]", "Join button text"),
            ("CSS", "button[jsname='Qx7uuf']", "Google jsname button"),
            ("CSS", "button[aria-label*='Join' i]", "Join aria-label")
        ]
        
        for method, selector, description in join_methods:
            try:
                if method == "XPATH":
                    element = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    element = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                if element.is_displayed() and element.is_enabled():
                    element.click()
                    print(f"✅ Clicked: {description}")
                    time.sleep(5)
                    return True
                    
            except TimeoutException:
                continue
            except Exception:
                continue
        
        # Fallback: Enter key
        try:
            print("🔄 Trying Enter key fallback...")
            body = self.browser.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.ENTER)
            time.sleep(5)
            return True
        except:
            return False

    def join_meeting(self, url):
        """Join meeting with Chrome audio access, bot silence, and visible mic indicator"""
        if not self.setup_browser():
            return False
        
        if not self.navigate_to_meet(url):
            return False
        
        # Keep bot silent but show mic indicator and allow Chrome to hear meeting
        self.force_complete_silence()
        
        if not self.click_join():
            print("❌ All join methods failed")
            return False
        
        self.is_active = True
        print("✅ Meeting joined successfully (BOT SILENT, MIC INDICATOR VISIBLE)")
        
        # Mute only bot, keep mic indicator, allow system recording
        time.sleep(3)
        self.mute_bot_audio()
        self.force_complete_silence()
        
        # Extract participant names
        time.sleep(5)
        self.participant_names = self.extract_real_participants()
        
        return True

    def is_meeting_active(self):
        try:
            return self.is_active and "meet" in self.browser.current_url
        except:
            return False

    def quit(self):
        try:
            if self.browser:
                self.browser.quit()
                print("🌐 Browser closed")
                
            # Cleanup temp profiles
            import shutil
            temp_dirs = [d for d in os.listdir('.') if d.startswith('temp_chrome_profile_')]
            for temp_dir in temp_dirs:
                try:
                    shutil.rmtree(temp_dir)
                    print(f"🗑️ Cleaned temp profile: {temp_dir}")
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
