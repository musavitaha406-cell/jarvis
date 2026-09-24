from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import sounddevice as sd
import numpy as np
import pyttsx3
import datetime
import os
import json
import threading
import tkinter as tk
from vosk import Model, KaldiRecognizer


X_train = [
    "ساعت چنده", "الان ساعت چیه", "بگو ساعت چنده",
    "کروم رو باز کن", "گوگل کروم رو باز کن", "مرورگر رو باز کن",
    "نوت پد رو باز کن", "نوت‌پد باز کن",
    "ماشین حساب رو باز کن", "کلکولاتور رو باز کن",
]
y_train = [
    "time", "time", "time",
    "open_chrome", "open_chrome", "open_chrome",
    "open_notepad", "open_notepad",
    "open_calc", "open_calc",
    
]
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X_train)
clf = SVC(kernel='linear')
clf.fit(X_vec, y_train)

# ============ 2. Text-to-speech ============
engine = pyttsx3.init()
engine.setProperty('rate', 175)

def speak(text):
    print(f"[Assistant]: {text}")
    ui.set_state("speaking", text)
    engine.say(text)
    engine.runAndWait()
    ui.set_state("idle", "در انتظار کلمه بیدارکننده...")

MODEL_PATH = "model"  
SAMPLE_RATE = 16000
WAKE_WORD = "جارویس"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Vosk model folder not found at '{MODEL_PATH}'. "
        "Download vosk-model-small-fa-0.42.zip, extract it, and rename the folder to 'model'."
    )

vosk_model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

awake = False 

def audio_callback(indata, frames, time_info, status):
    
    samples = np.frombuffer(indata, dtype=np.int16)

    
    volume = np.sqrt(np.mean(samples.astype(np.float32) ** 2)) / 32768.0
    ui.update_volume(volume)

    if recognizer.AcceptWaveform(bytes(indata)):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip()
        if text:
            handle_recognized_text(text)

def handle_recognized_text(text):
    global awake
    print(f"[Heard]: {text}")

    if not awake:
        if WAKE_WORD in text:
            awake = True
            ui.set_state("listening", "بله؟ در انتظار دستور...")
            speak("بله؟")
        return


    awake = False
    if "خاموش شو" in text or "بسته شو" in text:
        speak("خاموش می‌شوم")
        os._exit(0)
    run_command(text)

# ============ Command functions ============
def get_time():
    now = datetime.datetime.now()
    return f"الان ساعت {now.hour} و {now.minute} دقیقه‌ست"

def open_chrome():
    os.system("start chrome")
    return "کروم رو باز کردم"

def open_notepad():
    os.system("start notepad")
    return "نوت‌پد رو باز کردم"

def open_calc():
    os.system("start calc")
    return "ماشین حساب رو باز کردم"
def open_vs():
    os.system('start vs code')
    return "vs code is open"

intent_functions = {
    "time": get_time,
    "open_chrome": open_chrome,
    "open_notepad": open_notepad,
    "open_calc": open_calc,
    "open_vs" :open_vs
}

def run_command(text):
    ui.set_state("thinking", "در حال پردازش...")
    predicted_intent = clf.predict(vectorizer.transform([text]))[0]
    if predicted_intent in intent_functions:
        result = intent_functions[predicted_intent]()
        speak(result)
    else:
        speak("متوجه نشدم")

# ============ 5. Background audio stream (runs in a separate thread) ============
def audio_loop():
    ui.set_state("idle", "در انتظار کلمه بیدارکننده...")
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                            dtype='int16', channels=1, callback=audio_callback):
        while True:
            sd.sleep(100)


class JarvisUI:
    COLORS = {
        "idle": "#45A29E",       # teal
        "listening": "#66FCF1",  # bright cyan
        "thinking": "#FFB800",   # amber
        "speaking": "#00E0FF",   # electric blue
    }
    BG = "#0B0C10"
    PANEL = "#1F2833"

    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg=self.BG)
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=420, height=380, bg=self.BG, highlightthickness=0)
        self.canvas.pack()

        self.status_label = tk.Label(root, text="در حال بارگذاری...", fg="#C5C6C7",
                                      bg=self.BG, font=("Consolas", 12))
        self.status_label.pack(pady=8)

        self.current_color = self.COLORS["idle"]
        self.angle = 0
        self.volume_level = 0.0
        self.bars = []

        cx, cy = 210, 190
        # Outer rotating ring made of arc segments (HUD look)
        self.ring_items = []
        for i in range(8):
            arc = self.canvas.create_arc(cx-140, cy-140, cx+140, cy+140,
                                          start=i*45+10, extent=25,
                                          style="arc", outline=self.current_color, width=2)
            self.ring_items.append(arc)

        # Middle ring
        self.mid_ring = self.canvas.create_oval(cx-95, cy-95, cx+95, cy+95,
                                                  outline=self.current_color, width=1)

        # Core circle (pulses)
        self.core = self.canvas.create_oval(cx-60, cy-60, cx+60, cy+60,
                                             outline=self.current_color, width=3)
        self.core_glow = self.canvas.create_oval(cx-60, cy-60, cx+60, cy+60,
                                                  fill=self.current_color, outline="",
                                                  stipple="gray25")

        
        bar_count = 20
        bar_width = 12
        start_x = cx - (bar_count * bar_width) // 2
        for i in range(bar_count):
            x = start_x + i * bar_width
            bar = self.canvas.create_rectangle(x, cy+150, x+bar_width-3, cy+150,
                                                fill=self.current_color, outline="")
            self.bars.append(bar)

        self.pulse = 0
        self.growing = True
        self.cx, self.cy = cx, cy
        self.animate()

    def set_state(self, state, text):
        self.current_color = self.COLORS.get(state, self.COLORS["idle"])
        self.status_label.config(text=text)

    def update_volume(self, volume):
        self.volume_level = min(volume * 15, 1.0)  

    def animate(self):
        cx, cy = self.cx, self.cy

        
        self.angle = (self.angle + 1) % 360
        for i, arc in enumerate(self.ring_items):
            self.canvas.itemconfig(arc, outline=self.current_color)
            self.canvas.coords(arc, cx-140, cy-140, cx+140, cy+140)
            self.canvas.itemconfig(arc, start=self.angle + i*45)

        
        self.pulse += 1.5 if self.growing else -1.5
        if self.pulse >= 10:
            self.growing = False
        elif self.pulse <= 0:
            self.growing = True
        r = 60 + self.pulse
        self.canvas.coords(self.core, cx-r, cy-r, cx+r, cy+r)
        self.canvas.coords(self.core_glow, cx-r+8, cy-r+8, cx+r-8, cy+r-8)
        self.canvas.itemconfig(self.core, outline=self.current_color)
        self.canvas.itemconfig(self.core_glow, fill=self.current_color)
        self.canvas.itemconfig(self.mid_ring, outline=self.current_color)

     
        import random
        mid = len(self.bars) // 2
        for i, bar in enumerate(self.bars):
            falloff = 1 - (abs(i - mid) / mid)
            height = int(self.volume_level * 80 * falloff * random.uniform(0.5, 1.0))
            x0, y0, x1, y1 = self.canvas.coords(bar)
            self.canvas.coords(bar, x0, cy+150 - height, x1, cy+150)
            self.canvas.itemconfig(bar, fill=self.current_color)

        self.root.after(30, self.animate)

# ============ Start everything ============
root = tk.Tk()
ui = JarvisUI(root)

threading.Thread(target=audio_loop, daemon=True).start()

root.mainloop()
