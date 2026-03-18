from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, date
import json, os

app = Flask(__name__)
app.secret_key = "smartmess2026"

HOSTEL_NAME    = "Ruchi Hostel"
TOTAL_STUDENTS = 500
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

DATA_DIR         = "data"
STUDENTS_FILE    = os.path.join(DATA_DIR, "students.json")
FEEDBACK_FILE    = os.path.join(DATA_DIR, "feedback.json")
ATTENDANCE_FILE  = os.path.join(DATA_DIR, "attendance.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

STUDENTS      = load_json(STUDENTS_FILE, {})
FEEDBACK_LIST = load_json(FEEDBACK_FILE, [])
ALL_ATTENDANCE = load_json(ATTENDANCE_FILE, [])

WEEKLY_MENU = {
    0: {"breakfast": {"veg": ["Idli", "Sambar", "Coconut Chutney", "Pongal"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Dal Tadka", "Rasam", "Papad"], "nonveg": ["Chicken Curry", "Egg Gravy"]},
        "dinner":    {"veg": ["Chapati", "Paneer Masala", "Jeera Rice", "Dal"], "nonveg": ["Mutton Curry", "Fish Fry"]}},
    1: {"breakfast": {"veg": ["Pongal", "Vada", "Sambar", "Chutney"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Sambar", "Kootu", "Pickle", "Curd"], "nonveg": ["Fish Fry", "Prawn Masala"]},
        "dinner":    {"veg": ["Roti", "Dal Makhani", "Veg Biryani", "Raita"], "nonveg": ["Chicken Biryani", "Boiled Egg"]}},
    2: {"breakfast": {"veg": ["Dosa", "Sambar", "Tomato Chutney", "Coconut Chutney"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Rasam", "Beans Curry", "Curd", "Papad"], "nonveg": ["Egg Curry", "Chicken 65"]},
        "dinner":    {"veg": ["Chapati", "Aloo Gobi", "Dal Fry", "Jeera Rice"], "nonveg": ["Fish Curry", "Prawn Fry"]}},
    3: {"breakfast": {"veg": ["Upma", "Coconut Chutney", "Banana", "Coffee"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Dal", "Cabbage Fry", "Papad", "Pickle"], "nonveg": ["Mutton Biryani", "Boiled Egg"]},
        "dinner":    {"veg": ["Puri", "Chana Masala", "Khichdi", "Curd"], "nonveg": ["Chicken Roast", "Egg Bhurji"]}},
    4: {"breakfast": {"veg": ["Idli", "Podi", "Sambar", "Chutney"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Lemon Rice", "Mor Kuzhambu", "Papad"], "nonveg": ["Prawn Fry", "Egg Bhurji"]},
        "dinner":    {"veg": ["Chapati", "Paneer Butter Masala", "Curd Rice", "Dal"], "nonveg": ["Mutton Pepper Fry", "Fish Fry"]}},
    5: {"breakfast": {"veg": ["Rava Dosa", "Onion Chutney", "Sambar", "Coffee"], "nonveg": []},
        "lunch":     {"veg": ["Veg Biryani", "Raita", "Brinjal Curry", "Papad"], "nonveg": ["Chicken Biryani", "Boiled Egg"]},
        "dinner":    {"veg": ["Parota", "Kurma", "Veg Pulao", "Pickle"], "nonveg": ["Fish Fry", "Mutton Gravy"]}},
    6: {"breakfast": {"veg": ["Poori", "Potato Curry", "Halwa", "Tea"], "nonveg": []},
        "lunch":     {"veg": ["Rice", "Sambar", "Avial", "Payasam", "Papad"], "nonveg": ["Chicken Curry", "Fish Curry"]},
        "dinner":    {"veg": ["Chapati", "Kadai Paneer", "Fried Rice", "Dal"], "nonveg": ["Chicken 65", "Egg Fried Rice"]}},
}

SLOT_OPTIONS = {
    "breakfast": ["6:30 - 7:20", "7:20 - 8:10", "8:10 - 9:00"],
    "lunch":     ["11:00 - 11:50", "11:50 - 12:40", "12:40 - 1:30"],
    "dinner":    ["7:30 - 8:20", "8:20 - 9:10", "9:10 - 10:00"],
}

def fresh_day_data():
    return {
        "votes": {
            "breakfast": {"yes": 0, "no": 0},
            "lunch":     {"yes": 0, "no": 0},
            "dinner":    {"yes": 0, "no": 0},
        },
        "slots": {
            "breakfast": {"6:30 - 7:20": 0, "7:20 - 8:10": 0, "8:10 - 9:00": 0},
            "lunch":     {"11:00 - 11:50": 0, "11:50 - 12:40": 0, "12:40 - 1:30": 0},
            "dinner":    {"7:30 - 8:20": 0, "8:20 - 9:10": 0, "9:10 - 10:00": 0},
        },
        "student_votes":     {},
        "booked_students":   {},
        "attended_students": set(),
        "attendance_log":    [],
        "date": str(date.today()),
    }

DAY_DATA = fresh_day_data()

def save_attendance_to_file():
    global ALL_ATTENDANCE
    today = str(date.today())
    ALL_ATTENDANCE = [a for a in ALL_ATTENDANCE if a.get("date") != today]
    ALL_ATTENDANCE.extend(DAY_DATA["attendance_log"])
    save_json(ATTENDANCE_FILE, ALL_ATTENDANCE)

def reset_if_new_day():
    global DAY_DATA
    if DAY_DATA["date"] != str(date.today()):
        save_attendance_to_file()
        DAY_DATA = fresh_day_data()

def today_menu():
    return WEEKLY_MENU[datetime.now().weekday()]

def predict_food(meal):
    y = DAY_DATA["votes"][meal]["yes"]
    n = DAY_DATA["votes"][meal]["no"]
    return round(y + (n * 0.7))

def get_student(reg):
    return STUDENTS.get(reg.upper().strip())

def has_voted(reg, meal):
    return reg in DAY_DATA["student_votes"] and meal in DAY_DATA["student_votes"].get(reg, {})

def get_vote(reg, meal):
    return DAY_DATA["student_votes"].get(reg, {}).get(meal)

def has_booked(reg, meal):
    return reg in DAY_DATA["booked_students"] and meal in DAY_DATA["booked_students"].get(reg, {})

def get_booking(reg, meal):
    return DAY_DATA["booked_students"].get(reg, {}).get(meal)

def has_attended(reg, meal):
    return f"{reg}_{meal}" in DAY_DATA["attended_students"]

def get_absent_list():
    absent = []
    for reg, meal_votes in DAY_DATA["student_votes"].items():
        for meal, choice in meal_votes.items():
            if choice == "yes" and not has_attended(reg, meal):
                s = get_student(reg) or {}
                absent.append({
                    "name":  s.get("name", reg),
                    "reg":   reg,
                    "email": s.get("email", "-"),
                    "meal":  meal,
                    "slot":  get_booking(reg, meal) or "Not booked",
                })
    return absent

def student_logged_in():
    return "reg" in session and session.get("role") == "student"

def admin_logged_in():
    return session.get("role") == "admin"

@app.route("/")
def home():
    return redirect(url_for("register"))

@app.route("/register", methods=["GET", "POST"])
def register():
    reset_if_new_day()
    if student_logged_in():
        return redirect(url_for("student_home"))
    error = None
    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        reg   = request.form.get("reg", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        if not name or not reg or not email:
            error = "All fields are required!"
        elif "@" not in email:
            error = "Enter a valid college email!"
        elif get_student(reg):
            error = f"Reg No {reg} already registered! Please login."
        elif any(s["email"] == email for s in STUDENTS.values()):
            error = "Email already registered! Please login."
        else:
            STUDENTS[reg] = {
                "name": name, "reg": reg, "email": email,
                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            save_json(STUDENTS_FILE, STUDENTS)
            session["name"]  = name
            session["reg"]   = reg
            session["email"] = email
            session["role"]  = "student"
            return redirect(url_for("student_home"))
    return render_template("register.html", hostel=HOSTEL_NAME, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    reset_if_new_day()
    if student_logged_in():
        return redirect(url_for("student_home"))
    error = None
    if request.method == "POST":
        reg   = request.form.get("reg", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        student = get_student(reg)
        if not student:
            error = "Reg No not found! Please register first."
        elif student["email"] != email:
            error = "Incorrect email! Try again."
        else:
            session["name"]  = student["name"]
            session["reg"]   = student["reg"]
            session["email"] = student["email"]
            session["role"]  = "student"
            return redirect(url_for("student_home"))
    return render_template("login.html", hostel=HOSTEL_NAME, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student")
def student_home():
    reset_if_new_day()
    if not student_logged_in():
        return redirect(url_for("login"))
    reg  = session["reg"]
    menu = today_menu()
    meal_status = {}
    for m in ["breakfast", "lunch", "dinner"]:
        meal_status[m] = {
            "my_vote":  get_vote(reg, m),
            "booked":   has_booked(reg, m),
            "slot":     get_booking(reg, m),
            "attended": has_attended(reg, m),
        }
    return render_template("student_home.html",
        name=session["name"], reg=reg,
        hostel=HOSTEL_NAME, menu=menu,
        votes=DAY_DATA["votes"], slots=DAY_DATA["slots"],
        slot_options=SLOT_OPTIONS, now=datetime.now(),
        meal_status=meal_status,
        predict_breakfast=predict_food("breakfast"),
        predict_lunch=predict_food("lunch"),
        predict_dinner=predict_food("dinner"),
        today_date=str(date.today()),
    )

@app.route("/my_attendance")
def my_attendance():
    reset_if_new_day()
    if not student_logged_in():
        return redirect(url_for("login"))
    reg  = session["reg"]
    my_logs = [a for a in DAY_DATA["attendance_log"] if a["reg"] == reg]
    my_history = [a for a in ALL_ATTENDANCE if a["reg"] == reg and a.get("date") != str(date.today())]
    my_absent = []
    for meal, choice in DAY_DATA["student_votes"].get(reg, {}).items():
        if choice == "yes" and not has_attended(reg, meal):
            my_absent.append({
                "meal": meal,
                "slot": get_booking(reg, meal) or "Not booked",
            })
    return render_template("my_attendance.html",
        name=session["name"], reg=reg,
        hostel=HOSTEL_NAME,
        my_logs=my_logs,
        my_history=my_history,
        my_absent=my_absent,
        now=datetime.now(),
    )

@app.route("/vote", methods=["POST"])
def vote():
    reset_if_new_day()
    if not student_logged_in():
        return jsonify({"status": "error", "message": "Not logged in"})
    reg    = session["reg"]
    meal   = request.form.get("meal")
    choice = request.form.get("vote")
    prev   = get_vote(reg, meal)
    if prev:
        DAY_DATA["votes"][meal][prev] = max(0, DAY_DATA["votes"][meal][prev] - 1)
        if has_booked(reg, meal):
            old_slot = get_booking(reg, meal)
            if old_slot and old_slot in DAY_DATA["slots"][meal]:
                DAY_DATA["slots"][meal][old_slot] = max(0, DAY_DATA["slots"][meal][old_slot] - 1)
            DAY_DATA["booked_students"].get(reg, {}).pop(meal, None)
    if meal in DAY_DATA["votes"] and choice in ("yes", "no"):
        DAY_DATA["votes"][meal][choice] += 1
        DAY_DATA["student_votes"].setdefault(reg, {})[meal] = choice
        return jsonify({
            "status": "ok", "choice": choice,
            "yes": DAY_DATA["votes"][meal]["yes"],
            "no":  DAY_DATA["votes"][meal]["no"],
            "predicted": predict_food(meal),
        })
    return jsonify({"status": "error", "message": "Invalid data"})

@app.route("/book_slot", methods=["POST"])
def book_slot():
    reset_if_new_day()
    if not student_logged_in():
        return jsonify({"status": "error", "message": "Not logged in"})
    reg  = session["reg"]
    meal = request.form.get("meal")
    slot = request.form.get("slot")
    if has_booked(reg, meal):
        old_slot = get_booking(reg, meal)
        if old_slot and old_slot in DAY_DATA["slots"][meal]:
            DAY_DATA["slots"][meal][old_slot] = max(0, DAY_DATA["slots"][meal][old_slot] - 1)
        DAY_DATA["booked_students"].get(reg, {}).pop(meal, None)
    if not has_voted(reg, meal):
        return jsonify({"status": "error", "message": "Vote first!"})
    if get_vote(reg, meal) != "yes":
        return jsonify({"status": "error", "message": "Only YES voters can book!"})
    if meal in DAY_DATA["slots"] and slot in DAY_DATA["slots"][meal]:
        DAY_DATA["slots"][meal][slot] += 1
        DAY_DATA["booked_students"].setdefault(reg, {})[meal] = slot
        return jsonify({"status": "ok", "slot": slot})
    return jsonify({"status": "error", "message": "Invalid slot"})

@app.route("/attend/<reg>/<meal>/<qr_date>")
def attend_qr(reg, meal, qr_date):
    reset_if_new_day()
    reg = reg.upper().strip()
    if qr_date != str(date.today()):
        return render_template("attend_result.html",
            status="expired", message="QR Expired! Valid only for " + qr_date,
            student={}, hostel=HOSTEL_NAME)
    student = get_student(reg) or {"name": reg, "reg": reg, "email": "-"}
    name    = student.get("name", reg)
    slot    = get_booking(reg, meal) or "Not booked"
    key     = f"{reg}_{meal}"
    if key in DAY_DATA["attended_students"]:
        return render_template("attend_result.html",
            status="duplicate", message="Already entered!",
            student={"name": name, "reg": reg, "email": student.get("email","-"), "meal": meal, "slot": slot},
            hostel=HOSTEL_NAME)
    DAY_DATA["attended_students"].add(key)
    t = datetime.now().strftime("%H:%M:%S")
    record = {
        "name": name, "reg": reg,
        "email": student.get("email", "-"),
        "meal": meal, "slot": slot,
        "time": t, "date": str(date.today()),
    }
    DAY_DATA["attendance_log"].append(record)
    save_attendance_to_file()
    return render_template("attend_result.html",
        status="ok", message="Entry Allowed!",
        student={"name": name, "reg": reg, "email": student.get("email","-"),
                 "meal": meal, "slot": slot, "time": t},
        hostel=HOSTEL_NAME)

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    reset_if_new_day()
    if not admin_logged_in():
        return jsonify({"status": "error", "message": "Admin only!"})
    reg     = request.form.get("reg", "").strip().upper()
    meal    = request.form.get("meal", "").strip()
    qr_date = request.form.get("qr_date", "")
    if not reg or not meal:
        return jsonify({"status": "error", "message": "Invalid QR"})
    if qr_date != str(date.today()):
        return jsonify({"status": "error", "message": "QR expired!"})
    student = get_student(reg) or {"name": reg, "reg": reg, "email": "-"}
    name    = student.get("name", reg)
    slot    = get_booking(reg, meal) or "-"
    key     = f"{reg}_{meal}"
    if key in DAY_DATA["attended_students"]:
        return jsonify({"status": "duplicate", "message": "Already entered!",
                        "name": name, "reg": reg, "meal": meal, "slot": slot})
    DAY_DATA["attended_students"].add(key)
    t = datetime.now().strftime("%H:%M:%S")
    record = {
        "name": name, "reg": reg,
        "email": student.get("email", "-"),
        "meal": meal, "slot": slot,
        "time": t, "date": str(date.today()),
    }
    DAY_DATA["attendance_log"].append(record)
    save_attendance_to_file()
    return jsonify({"status": "ok", "message": "Entry allowed!",
                    "name": name, "reg": reg, "meal": meal, "slot": slot, "time": t})

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    if not student_logged_in():
        return redirect(url_for("login"))
    FEEDBACK_LIST.append({
        "name":    session.get("name", "Anonymous"),
        "reg":     session.get("reg", "-"),
        "rating":  int(request.form.get("rating", 3)),
        "comment": request.form.get("comment", ""),
        "meal":    request.form.get("meal", ""),
        "date":    str(date.today()),
    })
    save_json(FEEDBACK_FILE, FEEDBACK_LIST)
    return redirect(url_for("student_home"))

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if admin_logged_in():
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["role"]     = "admin"
            session["username"] = u
            return redirect(url_for("dashboard"))
        error = "Wrong username or password!"
    return render_template("admin_login.html", hostel=HOSTEL_NAME, error=error)

@app.route("/admin_logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/dashboard")
def dashboard():
    if not admin_logged_in():
        return redirect(url_for("admin_login"))
    reset_if_new_day()
    food_data = {
        m: {"yes": DAY_DATA["votes"][m]["yes"],
            "no":  DAY_DATA["votes"][m]["no"],
            "predicted": predict_food(m)}
        for m in DAY_DATA["votes"]
    }
    today_attendance = DAY_DATA["attendance_log"]
    history = [a for a in ALL_ATTENDANCE if a.get("date") != str(date.today())]
    return render_template("dashboard.html",
        votes=DAY_DATA["votes"], slots=DAY_DATA["slots"],
        food_data=food_data,
        attendance=today_attendance,
        history=history,
        absent_list=get_absent_list(),
        feedback=FEEDBACK_LIST,
        all_students=list(STUDENTS.values()),
        total_registered=len(STUDENTS),
        hostel=HOSTEL_NAME, now=datetime.now(),
    )

@app.route("/staff_scan")
def staff_scan():
    if not admin_logged_in():
        return redirect(url_for("admin_login"))
    return render_template("staff_scan.html", hostel=HOSTEL_NAME)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)