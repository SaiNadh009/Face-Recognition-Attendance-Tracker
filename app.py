"""
app.py
Flask backend for a face-recognition attendance tracker.

Endpoints:
  POST /enroll      - register a new person (name + photo)
  POST /recognize    - send a webcam frame, get back recognized name(s)
                        and auto-mark attendance
  GET  /attendance    - view today's attendance log

How it works:
  - Known faces are loaded from backend/known_faces/<name>.jpg at startup
  - face_recognition compares incoming frames against those known faces
  - A match above the confidence threshold is logged once per person per day

Run with: python app.py
"""

import csv
import os
from datetime import datetime

import cv2
import face_recognition
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

KNOWN_FACES_DIR = "known_faces"
ATTENDANCE_FILE = "attendance.csv"
MATCH_TOLERANCE = 0.5  # lower = stricter match

known_encodings = []
known_names = []


def load_known_faces():
    """Loads every image in known_faces/ and computes its face encoding."""
    known_encodings.clear()
    known_names.clear()

    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        return

    for filename in os.listdir(KNOWN_FACES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(os.path.splitext(filename)[0])

    print(f"Loaded {len(known_names)} known face(s): {known_names}")


def already_marked_today(name):
    if not os.path.exists(ATTENDANCE_FILE):
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    with open(ATTENDANCE_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0] == name and row[1].startswith(today):
                return True
    return False


def mark_attendance(name):
    is_new_file = not os.path.exists(ATTENDANCE_FILE)
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["name", "timestamp"])
        writer.writerow([name, datetime.now().isoformat()])


def decode_image_from_request(file_storage):
    file_bytes = np.frombuffer(file_storage.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


@app.route("/enroll", methods=["POST"])
def enroll():
    """Register a new person: form-data with 'name' and 'image' file."""
    name = request.form.get("name")
    image_file = request.files.get("image")

    if not name or not image_file:
        return jsonify({"error": "Both 'name' and 'image' are required"}), 400

    save_path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
    image_file.save(save_path)
    load_known_faces()

    return jsonify({"message": f"Enrolled '{name}' successfully"}), 200


@app.route("/recognize", methods=["POST"])
def recognize():
    """Send a single frame (form-data 'image'), get back recognized names."""
    image_file = request.files.get("image")
    if not image_file:
        return jsonify({"error": "'image' file is required"}), 400

    frame = decode_image_from_request(image_file)
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    results = []
    for encoding in face_encodings:
        name = "Unknown"
        if known_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_match_idx = int(np.argmin(distances))
            if distances[best_match_idx] <= MATCH_TOLERANCE:
                name = known_names[best_match_idx]

        marked = False
        if name != "Unknown" and not already_marked_today(name):
            mark_attendance(name)
            marked = True

        results.append({"name": name, "attendance_marked": marked})

    return jsonify({"recognized": results}), 200


@app.route("/attendance", methods=["GET"])
def attendance():
    """Returns today's attendance log."""
    if not os.path.exists(ATTENDANCE_FILE):
        return jsonify({"records": []}), 200

    today = datetime.now().strftime("%Y-%m-%d")
    records = []
    with open(ATTENDANCE_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["timestamp"].startswith(today):
                records.append(row)

    return jsonify({"records": records}), 200


if __name__ == "__main__":
    load_known_faces()
    app.run(host="0.0.0.0", port=5000, debug=True)
