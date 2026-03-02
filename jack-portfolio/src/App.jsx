import { useState, useEffect, useRef } from "react";
import profilePic from "./assets/profile.jpeg";
import { QRCodeCanvas } from "qrcode.react";

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [typedText, setTypedText] = useState("");
  const text = "Aspiring AI & Data Science Engineer";
  const i = useRef(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setTypedText(text.slice(0, i.current + 1));
      i.current += 1;
      if (i.current === text.length) clearInterval(timer);
    }, 100);
    return () => clearInterval(timer);
  }, []);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const bgColor = darkMode ? "#121212" : "#f5f5f5";
  const textColor = darkMode ? "#f5f5f5" : "#333";
  const cardBg = darkMode ? "#1e1e1e" : "#fff";

  const skills = ["Python", "Machine Learning", "React", "Git", "Data Science"];
  const projects = [
    "🎓 Student Dashboard System",
    "🤖 AI Face Recognition Project",
    "📊 Data Analysis Projects",
  ];

  return (
    <div
      style={{
        fontFamily: "Arial, sans-serif",
        minHeight: "100vh",
        backgroundColor: bgColor,
        color: textColor,
        transition: "0.3s",
        padding: "40px 20px",
        width: "100%",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      {/* Dark Mode Toggle */}
      <button
        onClick={toggleDarkMode}
        style={{
          position: "fixed",
          top: "20px",
          right: "20px",
          padding: "10px 15px",
          borderRadius: "5px",
          border: "none",
          cursor: "pointer",
          backgroundColor: "#0d6efd",
          color: "#fff",
        }}
      >
        {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
      </button>

      {/* Main container */}
      <div
        style={{
          maxWidth: "1200px",
          width: "95%",
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {/* Profile Picture */}
        <img
          src={profilePic}
          alt="Bhargavi"
          style={{
            width: "160px",
            height: "160px",
            borderRadius: "50%",
            objectFit: "cover",
            marginBottom: "20px",
            border: `4px solid #0d6efd`,
            animation: "bounce 2s infinite",
          }}
        />

        {/* Header */}
        <h1 style={{ fontSize: "2.8rem", marginBottom: "10px", color: "#0d6efd", textAlign: "center" }}>
          Hi, I'm Bhargavi 👋
        </h1>
        <h2 style={{ fontWeight: "400", marginBottom: "20px", minHeight: "30px", textAlign: "center" }}>
          {typedText}
          <span style={{ borderRight: "2px solid", marginLeft: "2px" }}></span>
        </h2>

        <p style={{ maxWidth: "900px", textAlign: "center", lineHeight: "1.6", marginBottom: "30px" }}>
          Passionate about Artificial Intelligence, Machine Learning, and building
          real-world applications that solve real problems.
        </p>

        <hr style={{ width: "80%", margin: "40px 0", border: "0", borderTop: `1px solid ${darkMode ? "#444" : "#ccc"}` }} />

        {/* Skills */}
        <section style={{ marginBottom: "30px", width: "100%", maxWidth: "800px" }}>
          <h3>🚀 Skills</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%" }}>
            {skills.map((skill, idx) => (
              <div
                key={idx}
                style={{
                  padding: "10px 20px",
                  backgroundColor: cardBg,
                  borderRadius: "8px",
                  textAlign: "center",
                  fontWeight: "500",
                  width: "100%",
                  maxWidth: "300px",
                  margin: "0 auto",
                  boxSizing: "border-box",
                }}
              >
                {skill}
              </div>
            ))}
          </div>
        </section>

        {/* Projects */}
        <section style={{ marginBottom: "30px", width: "100%" }}>
          <h3>📂 Projects</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
              gap: "15px",
              width: "100%",
            }}
          >
            {projects.map((project, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: cardBg,
                  padding: "15px 20px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  transition: "0.3s",
                  textAlign: "center",
                  boxSizing: "border-box",
                }}
                onMouseEnter={(e) =>
                  (e.target.style.backgroundColor = darkMode ? "#333" : "#e0f0ff")
                }
                onMouseLeave={(e) =>
                  (e.target.style.backgroundColor = cardBg)
                }
              >
                {project}
              </div>
            ))}
          </div>
        </section>

        {/* Connect */}
        <section style={{ marginBottom: "30px", textAlign: "center" }}>
          <h3>🔗 Connect With Me</h3>
          <div style={{ display: "flex", gap: "20px", justifyContent: "center", flexWrap: "wrap" }}>
            <a
              href="https://github.com/PudiBhargavi"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#0d6efd", textDecoration: "none", fontWeight: "500" }}
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/snape-severus-a7b38a3a4"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#0d6efd", textDecoration: "none", fontWeight: "500" }}
            >
              LinkedIn
            </a>
          </div>
        </section>

        {/* QR Code */}
        <section style={{ margin: "40px 0", textAlign: "center" }}>
          <h3>📱 Scan to Visit My Portfolio</h3>
          <QRCodeCanvas
            value="https://your-vercel-deployment.vercel.app" // replace with actual URL
            size={200}
            bgColor={darkMode ? "#121212" : "#fff"}
            fgColor={darkMode ? "#fff" : "#000"}
            style={{ margin: "20px auto" }}
          />
        </section>
      </div>

      <footer style={{ marginTop: "50px", fontSize: "14px", textAlign: "center" }}>
        © {new Date().getFullYear()} Bhargavi — Built with React & ❤️
      </footer>

      {/* Bounce animation */}
      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }

        /* Media queries for mobile view */
        @media (max-width: 768px) {
          h1 { font-size: 2.2rem; }
          h2 { font-size: 1.4rem; }
          img { width: 130px; height: 130px; }
          section div { max-width: 100%; }
          section { padding: 0 10px; }
        }
      `}</style>
    </div>
  );
}

export default App;