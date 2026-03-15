import sys
import psutil
import os
import datetime # NEW: Gives the Brain a clock
from send2trash import send2trash # The new safety tool

class PetBrain:
    def __init__(self):
        self.hp = 100
        self.weight = 50
        self.status = "CHILLIN 😎"
        self.xp = 0
        self.is_dead = False
        self.overclocking = False 
        # --- FEATURE 4: SNOOPER MEMORY ---
        self.last_clipboard = "" 
        self.pet_thoughts = ""   
        self.active_url = ""      # Tracksclickable link
        self.thought_timer = 0

    def read_hardware(self):
        cpu_usage = psutil.cpu_percent(interval=0.1) 
        ram_usage = psutil.virtual_memory().percent
        
        battery = psutil.sensors_battery()
        plugged_in = True
        batt_percent = 100
        
        if battery:
            plugged_in = battery.power_plugged
            batt_percent = battery.percent if battery.percent is not None else 100
            
        return {
            "cpu": cpu_usage, 
            "ram": ram_usage,
            "battery": batt_percent,
            "plugged_in": plugged_in
        }

    # NEW: We now pass clipboard_text into the brain
    def update_stats(self, clipboard_text=""):
        if self.is_dead:
            return {
                "cpu": 0, "ram": 0, "hp": 0, "weight": self.weight, 
                "status": "FATAL ERROR 🪦", "battery": 0, 
                "plugged_in": False, "xp": self.xp, "title": "SYSTEM HALTED",
                "thoughts": "" # Dead pets don't think!
            }

        data = self.read_hardware()
        cpu = data["cpu"]
        ram = data["ram"]
        batt = data["battery"]
        plugged = data["plugged_in"]
        
        # --- FEATURE 3: CIRCADIAN RHYTHMS ---
        # Get the current hour (0-23 format)
        current_hour = datetime.datetime.now().hour
        # Late night is between 11 PM (23) and 6 AM (6)
        is_late_night = current_hour >= 23 or current_hour < 6 
        
        # --- FEATURE 4: SNOOPER LOGIC ---
        if clipboard_text and clipboard_text != self.last_clipboard:
            self.last_clipboard = clipboard_text
            self.thought_timer = 30 # Keep thought on screen for 30 ticks (60 seconds)
            self.active_url = ""    # Reset url
            
            # The pet reacts based on what you copied
            if clipboard_text.startswith("http"):
                self.pet_thoughts = "SNOOP: Ooh, a website link! Where are we going?"
                self.active_url = clipboard_text # Save the URL for clicking
            elif len(clipboard_text.splitlines()) > 5:
                self.pet_thoughts = "SNOOP: That's a lot of code you just copied..."
            else:
                # Clean up the text so it fits on screen nicely
                clean_text = clipboard_text[:15].replace('\n', ' ')
                self.pet_thoughts = f"SNOOP: Copied '{clean_text}...'!"
        
        # Decay the thought timer so it eventually clears
        if self.thought_timer > 0:
            self.thought_timer -= 1
        else:
            self.pet_thoughts = ""
            self.active_url = "" # Clear the link when the thought disappears
        
        # Metabolism
        if ram > 80:
            self.weight += 1
        elif ram < 40:
            self.weight = max(10, self.weight - 1)
            
        # Core Game Logic with Time Awareness Overrides
        if self.overclocking:
            self.hp -= 4      
            self.xp += 5      
            self.status = "OVERCLOCK ⚡"
        elif not plugged and batt < 20:
            self.status = "LOW BATTERY 💤"
        elif cpu > 85:
            # NEW: If you stress the PC late at night, the pet gets CRANKY
            if is_late_night:
                self.hp -= 4 # Double damage for keeping it awake!
                self.status = "CRANKY 😠 (Let me sleep!)"
            else:
                self.hp -= 2
                self.status = "STRESSED 🥵"
        elif ram > 80:
            self.status = "CHONKY 🍔"
        elif is_late_night:
            # NEW: The default state late at night isn't Chillin, it's Sleepy
            self.status = "SLEEPY 😴" 
            # Removed self.xp += 1 to stop passive XP gain
        else:
            self.status = "CHILLIN 😎"
            # Removed self.xp += 1 to stop passive XP gain
            
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.overclocking = False 

        if self.xp < 50: title = "LVL 1: GUEST"
        elif self.xp < 150: title = "LVL 2: USER"
        elif self.xp < 500: title = "LVL 3: SYSADMIN"
        else: title = "LVL MAX: ROOT 👑"

        return {
            "cpu": cpu, "ram": ram, "hp": self.hp,
            "weight": self.weight, "status": self.status,
            "battery": batt, "plugged_in": plugged, 
            "xp": self.xp, "title": title,
            "thoughts": self.pet_thoughts, 
            "active_url": self.active_url # Tell the UI if there is a link to open
        }

    def get_top_offender(self):
        import getpass
        try:
            current_user = getpass.getuser()
        except:
            current_user = None

        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                # Try to fetch username to filter out SYSTEM processes
                try:
                    uname = p.username()
                    if current_user and uname and current_user not in uname:
                        continue
                except psutil.AccessDenied:
                    continue # Skip processes we don't have access to

                name = p.info['name']
                safe_list = ['System Idle Process', 'explorer.exe', 'svchost.exe', 'csrss.exe', 'python.exe', 'cmd.exe', 'powershell.exe', 'Code.exe']
                
                if name not in safe_list and p.info['memory_percent'] is not None:
                    procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if procs:
            return max(procs, key=lambda x: x['memory_percent'])
        return None

    def devour_process(self, pid):
        try:
            target = psutil.Process(pid)
            name = target.name()
            target.terminate() 
            self.weight = max(10, self.weight - 5)
            self.hp = min(100, self.hp + 10)
            return True, f"Devoured {name}! +10 HP"
        except psutil.AccessDenied:
            return False, "Access Denied: It's too strong!"
        except psutil.NoSuchProcess:
            return False, "Process vanished already."
        except Exception as e:
            return False, f"Indigestion: {str(e)}"

    def toggle_overclock(self):
        if not self.is_dead:
            self.overclocking = not self.overclocking

    def reboot_system(self):
        self.hp = 100
        self.weight = 50
        self.xp = 0
        self.is_dead = False
        self.overclocking = False
        self.status = "CHILLIN 😎"

    # --- NEW: FILE SCAVENGER LOGIC ---
    def eat_file(self, file_path):
        """Eats a physical file, sending it to the Recycle Bin for stats."""
        # Windows send2trash bug fix: convert all '/' to '\' because SHFileOperationW breaks on '/'
        file_path = os.path.normpath(file_path)
        
        # Remove extended path prefix if present, as send2trash/SHFileOperationW hates it
        if file_path.startswith("\\\\?\\"):
            file_path = file_path[4:]

        if not os.path.exists(file_path): 
            return False, "File not found."
        
        try:
            # Calculate file size in Megabytes
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Safely move it to the Recycle Bin
            send2trash(file_path) 
            
            # The Reward: Big files give huge HP boosts and weight loss
            weight_loss = max(1, int(size_mb / 10)) # Lose 1 WGT per 10MB
            hp_gain = max(5, int(size_mb / 5))      # Minimum 5 HP gain
            
            self.weight = max(10, self.weight - weight_loss)
            self.hp = min(100, self.hp + hp_gain)
            
            return True, f"Ate {size_mb:.1f}MB! Yum!"
        except Exception as e:
            return False, f"Could not eat file: {e}"
