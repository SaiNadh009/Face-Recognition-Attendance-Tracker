import React, { useEffect, useRef, useState } from "react";

const API_BASE = "http://localhost:5000";

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [status, setStatus] = useState("");
  const [enrollName, setEnrollName] = useState("");
  const [records, setRecords] = useState([]);

  // Start webcam on page load
  useEffect(() => {
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch(() => setStatus("Could not access webcam."));
  }, []);

  const captureFrame = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg");
    });
  };

  const handleEnroll = async () => {
    if (!enrollName.trim()) {
      setStatus("Enter a name before enrolling.");
      return;
    }
    setStatus("Capturing photo for enrollment...");
    const blob = await captureFrame();

    const formData = new FormData();
    formData.append("name", enrollName.trim());
    formData.append("image", blob, "enroll.jpg");

    const res = await fetch(`${API_BASE}/enroll`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    setStatus(res.ok ? data.message : `Error: ${data.error}`);
    setEnrollName("");
  };

  const handleRecognize = async () => {
    setStatus("Scanning face...");
    const blob = await captureFrame();

    const formData = new FormData();
    formData.append("image", blob, "frame.jpg");

    const res = await fetch(`${API_BASE}/recognize`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(`Error: ${data.error}`);
      return;
    }

    if (data.recognized.length === 0) {
      setStatus("No face detected. Try again.");
    } else {
      const summary = data.recognized
        .map((r) => (r.attendance_marked ? `${r.name} (marked present)` : `${r.name} (already marked / unknown)`))
        .join(", ");
      setStatus(summary);
      fetchAttendance();
    }
  };

  const fetchAttendance = async () => {
    const res = await fetch(`${API_BASE}/attendance`);
    const data = await res.json();
    setRecords(data.records || []);
  };

  useEffect(() => {
    fetchAttendance();
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Face Recognition Attendance Tracker</h1>

      <video ref={videoRef} autoPlay playsInline width="480" height="360" style={{ border: "1px solid #ccc" }} />
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div style={{ marginTop: 16 }}>
        <input
          type="text"
          placeholder="Name to enroll"
          value={enrollName}
          onChange={(e) => setEnrollName(e.target.value)}
        />
        <button onClick={handleEnroll} style={{ marginLeft: 8 }}>
          Enroll Face
        </button>
        <button onClick={handleRecognize} style={{ marginLeft: 8 }}>
          Mark Attendance
        </button>
      </div>

      <p style={{ marginTop: 12, fontWeight: "bold" }}>{status}</p>

      <h2>Today's Attendance</h2>
      <ul>
        {records.map((r, i) => (
          <li key={i}>
            {r.name} — {new Date(r.timestamp).toLocaleTimeString()}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
