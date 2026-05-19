import tkinter as tk
import serial
import mysql.connector
import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas   #  FIX 1

# =========================================================
# CONFIG
# =========================================================

with open("config.json", "r") as f:
    config = json.load(f)

def connect_serial():
    try:
        s = serial.Serial(config["serial_port"], config["baud_rate"], timeout=1)
        print("Serial Connected")
        return s
    except Exception as e:
        print("Serial Error:", e)
        return None

ser = connect_serial()

db_config = config["mysql"]
LEDGER_FOLDER = config["ledger_folder"]
os.makedirs(LEDGER_FOLDER, exist_ok=True)

# =========================================================
# SAFE RUN FLAG
# =========================================================

running = True

def on_close():
    global running
    running = False
    root.destroy()

# =========================================================
# AUTH SYSTEM
# =========================================================

AUTHORIZED_UID = "3A07203B"

def get_name(uid):
    return "ADMIN" if uid == AUTHORIZED_UID else "UNKNOWN"

# =========================================================
# STATS
# =========================================================

total_attempts = 0
granted = 0
denied = 0

# =========================================================
# DB LOG
# =========================================================

def insert_log(uid, status):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO access_logs (uid, status, timestamp) VALUES (%s, %s, %s)",
            (uid, status, datetime.now())
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print("DB ERROR:", e)

# =========================================================
# SERIAL PARSER
# =========================================================

last_uid = None

def parse_line(line):
    try:
        line = line.decode(errors="ignore").strip()

        if line.startswith("UID:"):
            uid = line.replace("UID:", "").strip()
            return uid, None

        if line in ["GRANTED", "DENIED"]:
            return None, line

        return None, None

    except:
        return None, None

# =========================================================
# UI
# =========================================================

root = tk.Tk()
root.title("RFID SMART SYSTEM")
root.geometry("1100x750")
root.configure(bg="#1e1e1e")
root.protocol("WM_DELETE_WINDOW", on_close)

# =========================================================
# HEADER
# =========================================================

header = tk.Label(root, text="RFID ACCESS CONTROL DASHBOARD",
                  font=("Arial", 18, "bold"),
                  bg="#2d2d2d", fg="white", pady=10)
header.pack(fill="x")

# =========================================================
# TOP BAR
# =========================================================

top_frame = tk.Frame(root, bg="#1e1e1e")
top_frame.pack(fill="x")

clock_label = tk.Label(top_frame, font=("Arial", 12), fg="cyan", bg="#1e1e1e")
clock_label.pack(side="left", padx=10)

status_label = tk.Label(top_frame, text="SYSTEM READY",
                        font=("Arial", 14, "bold"),
                        fg="white", bg="#1e1e1e")
status_label.pack(side="right")

status_indicator = tk.Label(top_frame, text="●", font=("Arial", 20),
                            fg="yellow", bg="#1e1e1e")
status_indicator.pack(side="right", padx=10)

# =========================================================
# STATS
# =========================================================

stats_label = tk.Label(root, text="Total: 0 | Granted: 0 | Denied: 0",
                       font=("Arial", 12),
                       fg="white", bg="#1e1e1e")
stats_label.pack(pady=5)

# =========================================================
# BUTTON FRAME
# =========================================================

btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(fill="x", pady=5)

# =========================================================
# LOG AREA
# =========================================================

log_frame = tk.Frame(root, bg="#1e1e1e")
log_frame.pack(fill="both", expand=True)

text = tk.Text(log_frame, bg="#111111", fg="white")
text.pack(side="left", fill="both", expand=True)

scrollbar = tk.Scrollbar(log_frame, command=text.yview)
scrollbar.pack(side="right", fill="y")

text.config(yscrollcommand=scrollbar.set)

text.tag_config("GRANTED", foreground="green")
text.tag_config("DENIED", foreground="red")

logs = []

# =========================================================
# GRAPH
# =========================================================

graph_frame = tk.Frame(root, bg="#1e1e1e")
graph_frame.pack(fill="x")

fig, ax = plt.subplots()
fig_canvas = FigureCanvasTkAgg(fig, master=graph_frame)   #  FIX 2
fig_canvas.get_tk_widget().pack()

def update_graph():
    if not running:
        return

    ax.clear()
    ax.bar(["Granted", "Denied"], [granted, denied],
           color=["green", "red"])
    ax.set_title("Live Access Attempts")
    ax.set_ylabel("Count")
    fig_canvas.draw()

    root.after(1000, update_graph)

update_graph()

# =========================================================
# CLOCK
# =========================================================

def update_clock():
    if not running:
        return

    clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
    root.after(1000, update_clock)

update_clock()

# =========================================================
# MAIN LOOP
# =========================================================

def update():
    global ser, last_uid, total_attempts, granted, denied

    if not running:
        return

    try:
        if ser and ser.in_waiting:
            raw = ser.readline()

            uid, status = parse_line(raw)

            if uid:
                last_uid = uid

            if status and last_uid:

                name = get_name(last_uid)

                msg = f"[{datetime.now().strftime('%Y-%m-%d')}] {last_uid} | {name} | {status}"

                logs.append([datetime.now().strftime("%H:%M:%S"), msg])

                tag = "GRANTED" if status == "GRANTED" else "DENIED"
                text.insert(tk.END, msg + "\n", tag)
                text.see(tk.END)

                insert_log(last_uid, status)

                total_attempts += 1

                if status == "GRANTED":
                    granted += 1
                    status_label.config(text=f"{name} | GRANTED", fg="lightgreen")
                    status_indicator.config(fg="green")
                else:
                    denied += 1
                    status_label.config(text=f"{name} | DENIED", fg="red")
                    status_indicator.config(fg="red")

                stats_label.config(
                    text=f"Total: {total_attempts} | Granted: {granted} | Denied: {denied}"
                )

                last_uid = None

    except Exception as e:
        print("ERROR:", e)

    root.after(200, update)

update()

# =========================================================
# PDF EXPORT
# =========================================================

def save_graph_image():
    fig2, ax2 = plt.subplots()

    ax2.bar(["Granted", "Denied"], [granted, denied],
            color=["green", "red"])

    ax2.set_title("Access Summary")
    ax2.set_ylabel("Count")

    path = "rfid_graph.png"
    fig2.savefig(path)
    plt.close(fig2)

    return path

def export_pdf():
    file = "RFID_Security_Report.pdf"
    c = pdf_canvas.Canvas(file, pagesize=A4)   #  FIX 3

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 820, "RFID SECURITY SYSTEM REPORT")

    c.setFont("Helvetica", 11)
    c.drawString(50, 800, f"Generated: {datetime.now()}")

    c.drawString(50, 780, f"Total Attempts: {total_attempts}")
    c.drawString(50, 765, f"Granted: {granted}")
    c.drawString(50, 750, f"Denied: {denied}")

    graph_path = save_graph_image()
    c.drawImage(graph_path, 50, 450, width=500, height=200)

    y = 420
    c.setFont("Helvetica", 9)

    for l in logs[-25:]:
        if y < 50:
            c.showPage()
            y = 800
        c.drawString(50, y, str(l))
        y -= 15

    c.save()
    print("Security Report Generated")

# =========================================================
# BUTTON
# =========================================================

tk.Button(btn_frame, text="Export Security Report",
          command=export_pdf,
          bg="#444", fg="white").pack(side="left", padx=5)

# =========================================================
# START
# =========================================================

root.mainloop()
