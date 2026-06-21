# Face Recognition Attendance Tracker

A webcam-based attendance system: enroll a person's face once, then recognize
them automatically and log attendance — no manual sign-in sheet.

## How it works
- **Backend (Flask):** loads known faces from `backend/known_faces/`, exposes
  `/enroll`, `/recognize`, and `/attendance` endpoints using the
  `face_recognition` library (built on top of OpenCV/dlib).
- **Frontend (React):** captures frames from your webcam in the browser and
  sends them to the backend to enroll people or mark attendance.

## Requirements
- Python 3.9+
- Node.js 16+
- A webcam
- `cmake` installed on your system (required to build `dlib`, a dependency
  of `face_recognition`)

## Backend setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

This starts the API at `http://localhost:5000`.

## Frontend setup

```bash
cd frontend
npm install
npm start
```

This opens the app at `http://localhost:3000`.

## Usage
1. Open the app — it will ask for webcam permission.
2. Type a name in the input box and click **Enroll Face** to register that
   person (look straight at the camera).
3. Click **Mark Attendance** any time after that — it will recognize the
   face and log them as present (only once per day).
4. The "Today's Attendance" list updates automatically.

## Notes
- `face_recognition` can be tricky to install on Windows — installing
  `cmake` and Visual C++ Build Tools first usually fixes it. On Mac/Linux,
  `pip install cmake` followed by `pip install face_recognition` is usually
  enough.
- Attendance is stored in `backend/attendance.csv` (created automatically).

## Tech used
Flask, OpenCV, face_recognition (dlib), React
