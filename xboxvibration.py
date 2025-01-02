import ctypes
import time
import tkinter as tk
from tkinter import ttk
import threading
import random
import math
import xinput

try:
    xinput = ctypes.windll.xinput1_4
except AttributeError:
    xinput = ctypes.windll.xinput1_3

class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort),
    ]

def set_vibration(controller_id, left_motor, right_motor):
    vibration = XINPUT_VIBRATION(left_motor, right_motor)
    result = xinput.XInputSetState(controller_id, ctypes.pointer(vibration))
    if result != 0:
        raise RuntimeError(f"振動の設定に失敗しました (エラーコード: {result})")

def get_connected_controllers():
    controllers = []
    for i in range(4):
        if xinput.XInputGetState(i, ctypes.pointer(ctypes.c_uint32(0))) == 0:
            controllers.append(i)
    return controllers

class VibrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xbox 360 コントローラー振動制御")
        self.controller_id = None
        self.vibration_thread = None
        self.is_vibrating = False

        self.controller_label = tk.Label(root, text="接続されているコントローラー:")
        self.controller_label.pack()

        self.controller_combobox = ttk.Combobox(root)
        self.controller_combobox["values"] = [f"コントローラー {i}" for i in get_connected_controllers()]
        self.controller_combobox.pack()

        self.left_motor_label = tk.Label(root, text="左モーターの振動強度")
        self.left_motor_label.pack()
        self.left_motor_slider = tk.Scale(root, from_=0, to_=65535, orient="horizontal")
        self.left_motor_slider.pack()

        self.right_motor_label = tk.Label(root, text="右モーターの振動強度")
        self.right_motor_label.pack()
        self.right_motor_slider = tk.Scale(root, from_=0, to_=65535, orient="horizontal")
        self.right_motor_slider.pack()

        self.rhythm = ttk.Combobox(root)
        self.rhythm["values"] = ["自分で決める", "ウェーブ", "ランダム", "強弱"]
        self.rhythm.pack()
        self.rhythm.bind("<<ComboboxSelected>>", self.rhythm_selected)

        self.start_button = tk.Button(root, text="Start", command=self.start_vibration)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_vibration)
        self.stop_button.pack()

        self.log_text = tk.Text(root, height=10, width=50)
        self.log_text.pack()
        self.log_text.insert(tk.END, "ログ開始:\n")
        self.log_text.yview(tk.END)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)

    def start_vibration(self):
        if self.is_vibrating:
            self.log("振動はすでに開始されています。")
            return
        
        self.controller_id = self.controller_combobox.current()
        if self.controller_id == -1:
            self.log("コントローラーが選択されていません")
            return

        self.is_vibrating = True
        self.vibration_thread = threading.Thread(target=self.run_vibration)
        self.vibration_thread.start()

    def run_vibration(self):
        try:
            pattern = self.rhythm.get()
            time_step = 0  # 時間の経過を追跡
            while self.is_vibrating:
                left_motor = self.left_motor_slider.get()
                right_motor = self.right_motor_slider.get()

                if pattern == "ウェーブ":
                    # sin波によるウェーブ (2000から最大値まで)
                    wave_value = math.sin(time_step)  # -1から1までの値
                    left_motor = int(((wave_value * 0.5 + 0.5) * (65535 - 2000)) + 2000)
                    right_motor = left_motor

                elif pattern == "ランダム":
                    # ランダム振動
                    left_motor = random.randint(0, 65535)
                    right_motor = random.randint(0, 65535)

                elif pattern == "強弱":
                    # 強弱パターン
                    left_motor = 65535 if int(time_step) % 2 == 0 else 0
                    right_motor = 65535 if int(time_step) % 2 == 0 else 0

                set_vibration(self.controller_id, left_motor, right_motor)
                time_step += 0.1
                time.sleep(0.1)
        except Exception as e:
            self.log(f"エラー: {e}")
            self.stop_vibration()

    def stop_vibration(self):
        if not self.is_vibrating:
            self.log("振動はすでに停止しています。")
            return

        self.is_vibrating = False
        if self.vibration_thread is not None:
            self.vibration_thread.join()
        self.log(f"コントローラー {self.controller_id} の振動を停止します")
        set_vibration(self.controller_id, 0, 0)

    def rhythm_selected(self, event):
        pattern = self.rhythm.get()
        self.log(f"選択された振動パターン: {pattern}")

def main():
    root = tk.Tk()
    app = VibrationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
