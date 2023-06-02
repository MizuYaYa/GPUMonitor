import subprocess
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import time
import threading
import pandas as pd
import numpy as np
import cv2
from PIL import Image, ImageTk, ImageOps


#グラボの温度を取得
def get_gpu_temp():
    cmd = 'nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader'
    temp = int(subprocess.check_output(cmd))
    return temp
#print(f"get_gpu_temp: {get_gpu_temp()}")

#グラボを使用しているソフトをcsv形式で保存
def get_gpu_use_apps():
    cmd = 'nvidia-smi', '--query-compute-apps=name,pid', '--format=csv', '--filename=F:\programing\PycharmProject\GPUMonitor\src\gpu_use_apps_log.csv' #nvidia-smi --query-compute-apps=name,pid --format=csv --filename=F:\programing\PycharmProject\GPUMonitor\log.csv
    apps = subprocess.check_output(cmd)
    return apps
#print(f"get_gpu_use_apps: {get_gpu_use_apps()}")

#ソフトのpidをソフトの名前から取得します
def get_app_pid(app_name):
    df = pd.read_csv("gpu_use_apps_log.csv", sep=",", encoding="shift-jis")
    app = df[df["process_name"].str.contains(app_name)]
    reset_index_app = app.reset_index(drop=True)
    app_pid = reset_index_app.iat[0, 1]
    return app_pid
#print(f"get_app_pid: \n {get_app_pid('プロセス名')}")

#PIDを使用してタスクをキルします
def task_kill_using_pid(pid):
    cmd = 'taskkill', "/t", '/pid', f'{pid}', '/F'
    return subprocess.run(cmd, stdout=subprocess.PIPE, encoding="shift-jis")
#print(f"task_kill_using_pid: \n {task_kill_using_pid(get_app_pid('プロセス名'))}")

#app_name(タスク名)を使用してタスクをキルします
def task_kill_using_app_name(app_name):
    cmd = 'taskkill', '/im', f'{app_name}', '/F'
    return subprocess.run(cmd)

##################

max_gpu_temp = 85

gpu_temp_get_interval = 5

####

gpu_temp = 0

window_open = True

is_loop = True

is_standby = False

playing = True

root = Tk()

temp = IntVar(root)

process_name = StringVar(root)
max_temp = IntVar(root)

##################

def start_gpu_max_temp_limit(max_gpu_temp: int = 85, app_name: str = None):
    global is_loop, is_standby

    print(f"start_gpu_max_temp_limit: GPU温度監視を開始します。終了プロセス名は{app_name}、最大GPU温度は{max_gpu_temp}です。")

    while window_open and is_loop:
        if gpu_temp >= max_gpu_temp:
            is_standby = True
            break
        time.sleep(gpu_temp_get_interval)
    if is_standby:
        task_kill_return = task_kill_using_app_name(app_name)
        if task_kill_return.returncode == 0:
            print(f"start_gpu_max_temp_limit: {app_name}を正常に強制終了しました。\n 出力: {task_kill_return.stdout}")
            messagebox.showinfo("情報", f"{app_name}を正常に強制終了しました。\n 出力: {task_kill_return.stdout}")
        else:
            print(f"start_gpu_max_temp_limit: {app_name}が正常に強制終了されなかったかもしれません。終了コード: {task_kill_return.returncode} \n エラー内容: {task_kill_return.stderr}")
            messagebox.showwarning("警告...?", f"{app_name}を正常に強制終了できなかった可能性があります。終了コード: {task_kill_return.returncode} \n エラー内容: {task_kill_return.stdout}")
    else:
        print("start_gpu_max_temp_limit: GPU温度監視を停止します。")

def regular_gpu_temp():
    global gpu_temp
    while window_open:
        gpu_temp = get_gpu_temp()
        temp.set(gpu_temp)
        print(f"GPUTemp: {gpu_temp}")
        time.sleep(gpu_temp_get_interval)
    print(f"regular_gpu_temp: GPU温度の取得を停止します。")

def start_gui():

    def delete_window():
        global window_open
        window_open = False
        root.destroy()
        print("delete_window: Windowを削除しました。")

    root.title("GPUMonitor")
    root.geometry("640x360")
    root.iconphoto(False, PhotoImage(file="GPUMonitor.png"))
    root.protocol("WM_DELETE_WINDOW", delete_window)
    root.attributes("-topmost", True)

    start_credit()

    draw_frame()

    threading.Thread(target=regular_gpu_temp).start()

    root.mainloop()

global photo_image
def start_credit():
    global photo_image
    credit = Label(root, width=640, height=360, bg="black", relief="flat", bd=0)
    credit.grid(column=0, row=0, sticky="nsew")

    video = cv2.VideoCapture("bit.ly/3OTOfLF")
    def next_frame():
        global playing, photo_image
        ret, frame = video.read()
        if not ret:
            playing = False
        if ret:
            cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv_image)
            pil_image = ImageOps.pad(pil_image, (640, 360))
            photo_image = ImageTk.PhotoImage(image=pil_image)
            credit.config(image=photo_image)
            credit.photo_image = photo_image
    def video_frame_timer():
        print("credit_video start")
        time.sleep(0.5)
        credit.tkraise()
        while playing:
            next_frame()
            time.sleep(0.03)
        credit.destroy()
        print("credit_video end")
    def key_event(e):
        global playing
        key = e.keysym
        playing = False
        print(f"key_event: {key}キー入力があったためcredit_videoを停止します。")
    root.bind("<KeyPress>", key_event)
    threading.Thread(target=video_frame_timer, daemon=True).start()

def draw_frame():
    def start_btn_click():
        global is_loop
        stopping_label["bg"] = "#FFFFFF"
        start_btn["state"] = DISABLED
        input_process_name_entry["state"] = "readonly"
        input_max_temp_entry["state"] = "readonly"
        is_loop = True
        try:
            threading.Thread(target=start_gpu_max_temp_limit, args=(max_temp.get(), process_name.get())).start()
        except Exception as e:
            print(f"max_temp.get()はint型ではありません。: \n{e}")
            messagebox.showerror("エラー", f"テキストボックス  最大温度:°C  に数字以外を入力しないでください\n{e}")
            is_loop = False
            threading.Thread(target=stop_btn_click).start()
            max_temp.set(max_gpu_temp)
        else:
            print(f"max_gpu_temp: {max_temp.get()} :はint型です。")

        stop_btn["state"] = NORMAL
        operating_label["bg"] = "#008000"

    def stop_btn_click():
        global is_loop
        operating_label["bg"] = "#FFFFFF"
        stop_btn["state"] = DISABLED
        input_process_name_entry["state"] = "normal"
        input_max_temp_entry["state"] = "normal"
        is_loop = False
        start_btn["state"] = NORMAL
        stopping_label["bg"] = "#800000"

    font = "Yu Gothic UI"

    gpu_temp_frame = Frame(root, width=280, height=190, borderwidth=1, relief="solid")
    gpu_temp_label = Label(gpu_temp_frame, text=f"{gpu_temp}°C", font=(font, 64), textvariable=temp)
    temp_bar = ttk.Progressbar(gpu_temp_frame, maximum=110, mode="determinate", length=200, value=gpu_temp,variable=temp)
    #
    #
    operation_frame = Frame(root, width=280, height=100, borderwidth=1, relief="solid")
    #
    input_process_name_frame = Frame(operation_frame, width=150, height=40)
    stop_process_name_label = Label(input_process_name_frame, text="終了プロセス名", font=(font, 10))
    input_process_name_entry = ttk.Entry(input_process_name_frame, font=(font, 10), textvariable=process_name)
    #
    input_max_temp_frame = Frame(operation_frame, width=80, height=60)
    max_temp_label = Label(input_max_temp_frame, text="最大温度: °C", font=(font, 10))
    input_max_temp_entry = ttk.Entry(input_max_temp_frame, font=(font, 10), textvariable=max_temp)
    #
    start_stop_btn_frame = Frame(operation_frame, width=50, height=80)
    start_btn = ttk.Button(start_stop_btn_frame, text="開始", command=lambda :start_btn_click())
    stop_btn = ttk.Button(start_stop_btn_frame, text="停止", state=DISABLED, command=lambda :stop_btn_click())
    #
    operating_stopping_indicator_frame = Frame(operation_frame, width=90, height=20, borderwidth=1, relief="solid")
    operating_label = Label(operating_stopping_indicator_frame, text="動作中", font=(font, 10))
    stopping_label = Label(operating_stopping_indicator_frame, text="停止中", font=(font, 10), background="#800000")

    hogehoge_frame = Frame(root, width=300, height=300, borderwidth=1, relief="solid")


    gpu_temp_frame.propagate(False)
    operation_frame.propagate(False)
    input_max_temp_frame.propagate(False)
    start_stop_btn_frame.propagate(False)
    hogehoge_frame.propagate(False)

    gpu_temp_frame.grid(column=0, row=0, padx=(25, 5), pady=(30, 5))
    gpu_temp_label.pack()
    temp_bar.pack(pady=(10, 0))
    #
    #
    operation_frame.grid(column=0, row=1, padx=(25, 5), pady=(5, 30))
    #
    input_process_name_frame.pack(side=TOP, anchor=W, padx=5)
    stop_process_name_label.pack()
    input_process_name_entry.pack()
    #
    input_max_temp_frame.pack(side=BOTTOM, anchor=W, padx=5)
    max_temp_label.pack()
    input_max_temp_entry.pack()
    #
    start_stop_btn_frame.place(x=220, y=15)
    start_btn.pack(side=TOP, pady=(0, 10))
    stop_btn.pack(side=TOP, pady=(10, 0))
    #
    operating_stopping_indicator_frame.place(x=105, y=60)
    operating_label.pack(side=LEFT, padx=(0, 5))
    stopping_label.pack(side=LEFT)

    hogehoge_frame.grid(column=1, row=0, rowspan=2, padx=(5, 25), pady=(30, 30))

    max_temp.set(max_gpu_temp)

start_gui()