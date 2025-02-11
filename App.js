import React, { useState, useEffect, createContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useParams } from 'react-router-dom';
import './App.css';

// Theme Context
const ThemeContext = createContext();

// Layout Component
function Layout({ children }) {
  const { theme, toggleTheme } = React.useContext(ThemeContext);

  return (
    <div className={`app-container ${theme}`}>
      <header className="app-header">
        <div className="header-content">
          <h1 className="logo">SmartAttend</h1>
          <button onClick={toggleTheme} className="theme-toggle">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      <main className="main-content">{children}</main>

      <footer className="app-footer">
        <p>© 2023 SmartAttend. All rights reserved.</p>
        <p>Academic Attendance Management System</p>
      </footer>
    </div>
  );
}

// Index Page Component
function IndexPage() {
  return (
    <div className="index-page">
      <div className="hero-section">
        <h1>Modern Academic Attendance System</h1>
        <p>Streamline classroom management with AI-powered attendance tracking</p>
      </div>
      
      <div className="portal-links">
        <Link to="/teacher" className="portal-link teacher-link">
          Educator Portal
        </Link>
      </div>
    </div>
  );
}

// Student Component
function Student({ markAttendance, sessions }) {
  const { sessionId } = useParams();
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [sessionValid, setSessionValid] = useState(true);
  const [timeLeft, setTimeLeft] = useState('');
  const [locationError, setLocationError] = useState('');

  const currentSession = sessions.find(s => s.id === sessionId);

  useEffect(() => {
    if (!currentSession) {
      setSessionValid(false);
      return;
    }
  
    const interval = setInterval(() => {
      const now = new Date(); // Current time
      const start = new Date(currentSession.startTime); // Parse start time
      const end = new Date(start.getTime() + currentSession.duration * 60000); // Calculate end time
  
      if (now < start) {
        setTimeLeft(`Session starts in ${Math.round((start - now) / 1000)} seconds`);
      } else if (now > end) {
        setTimeLeft('Attendance period has ended');
        setSessionValid(false);
      } else {
        setTimeLeft(`Time remaining: ${Math.round((end - now) / 60000)} minutes`);
        setSessionValid(true); // Session is valid
      }
    }, 1000);
  
    return () => clearInterval(interval);
  }, [currentSession]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please enter your name.');
      return;
    }

    try {
      const position = await getCurrentPosition();
      const isInRange = checkLocationInRange(
        position.coords.latitude,
        position.coords.longitude,
        currentSession.location.lat,
        currentSession.location.lng,
        currentSession.location.radius
      );

      if (!isInRange) {
        setLocationError('You are not within the allowed location range.');
        return;
      }
    } catch (err) {
      setLocationError('Unable to retrieve your location. Please enable location services.');
      return;
    }

    const success = markAttendance(name.trim(), sessionId);
    if (success) {
      setName('');
      setError('');
      setLocationError('');
      alert('Attendance marked successfully!');
    } else {
      setError('You have already marked attendance for this session.');
    }
  };

  const getCurrentPosition = () => {
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject);
    });
  };

  const checkLocationInRange = (userLat, userLng, sessionLat, sessionLng, radius) => {
    const R = 6371e3;
    const φ1 = (userLat * Math.PI) / 180;
    const φ2 = (sessionLat * Math.PI) / 180;
    const Δφ = ((sessionLat - userLat) * Math.PI) / 180;
    const Δλ = ((sessionLng - userLng) * Math.PI) / 180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return (R * c) <= radius;
  };

  if (!sessionValid) {
    return (
      <div className="student-ui">
        <div className="session-alert">
          <h2>Invalid Session</h2>
          <p>This attendance session is either expired or does not exist.</p>
          <Link to="/" className="back-link">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="student-ui">
      <div className="attendance-container">
        <h1>Class Attendance</h1>
        <p className="session-timer">{timeLeft}</p>
        <form onSubmit={handleSubmit} className="attendance-form">
          <input
            type="text"
            placeholder="Enter your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          {error && <p className="error-message">{error}</p>}
          {locationError && <p className="error-message">{locationError}</p>}
          <button type="submit" className="btn-primary">
            Mark Attendance
          </button>
        </form>
        <Link to="/" className="back-link">
          Back to Home
        </Link>
      </div>
    </div>
  );
}

// Teacher Component
function Teacher({ sessions, createSession, attendance, deleteSession, deleteRecord, logout }) {
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [newSession, setNewSession] = useState({
    className: '',
    startTime: '',
    duration: 30,
    location: {
      lat: '',
      lng: '',
      radius: 100
    },
    autoLocation: false
  });
  const [selectedSession, setSelectedSession] = useState('all');

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === 'admin123') {
      setLoggedIn(true);
    } else {
      alert('Incorrect password. Please try again.');
    }
  };

  const handleCreateSession = (e) => {
    e.preventDefault();
    createSession(newSession);
    setNewSession({
      className: '',
      startTime: '',
      duration: 30,
      location: {
        lat: '',
        lng: '',
        radius: 100
      },
      autoLocation: false
    });
  };

  const handleLocationAutoDetect = () => {
    navigator.geolocation.getCurrentPosition(position => {
      setNewSession({
        ...newSession,
        location: {
          ...newSession.location,
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
      });
    });
  };

  const handleCopyLink = (link) => {
    navigator.clipboard.writeText(link).then(() => {
      alert('Link copied to clipboard!');
    });
  };

  const filteredAttendance = selectedSession === 'all' 
    ? attendance 
    : attendance.filter(entry => entry.sessionId === selectedSession);

  const sessionMap = sessions.reduce((map, session) => {
    map[session.id] = session;
    return map;
  }, {});

  if (!loggedIn) {
    return (
      <div className="teacher-auth">
        <div className="auth-container">
          <h1>Teacher Login</h1>
          <form onSubmit={handleLogin} className="login-form">
            <input
              type="password"
              placeholder="Enter admin password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button type="submit" className="btn-primary">
              Login
            </button>
          </form>
          <Link to="/" className="back-link">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="teacher-ui">
      <div className="management-container">
        <div className="teacher-header">
          <h1>Attendance Management</h1>
          <button onClick={logout} className="btn-danger">
            Logout
          </button>
        </div>

        <div className="session-management">
          <h2>Create New Class Session</h2>
          <form onSubmit={handleCreateSession} className="session-form">
            <div className="form-group">
              <input
                type="text"
                placeholder="Class Name"
                value={newSession.className}
                onChange={(e) => setNewSession({ ...newSession, className: e.target.value })}
                required
              />
            </div>
            
            <div className="form-group">
              <input
                type="datetime-local"
                value={newSession.startTime}
                onChange={(e) => setNewSession({ ...newSession, startTime: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <select
                value={newSession.duration}
                onChange={(e) => setNewSession({ ...newSession, duration: e.target.value })}
              >
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={45}>45 minutes</option>
                <option value={60}>60 minutes</option>
              </select>
            </div>

            <div className="location-section">
              <div className="location-toggle">
                <label>
                  <input
                    type="checkbox"
                    checked={newSession.autoLocation}
                    onChange={(e) => setNewSession({
                      ...newSession,
                      autoLocation: e.target.checked
                    })}
                  />
                  Use Current Location
                </label>
                <button 
                  type="button" 
                  className="btn-secondary"
                  onClick={handleLocationAutoDetect}
                  disabled={!newSession.autoLocation}
                >
                  Detect Location
                </button>
              </div>
              <div className="form-group">
                <input
                  type="number"
                  step="0.000001"
                  placeholder="Latitude"
                  value={newSession.location.lat}
                  onChange={(e) => setNewSession({ ...newSession, location: { ...newSession.location, lat: e.target.value } })}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="number"
                  step="0.000001"
                  placeholder="Longitude"
                  value={newSession.location.lng}
                  onChange={(e) => setNewSession({ ...newSession, location: { ...newSession.location, lng: e.target.value } })}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="number"
                  placeholder="Radius (meters)"
                  value={newSession.location.radius}
                  onChange={(e) => setNewSession({ ...newSession, location: { ...newSession.location, radius: e.target.value } })}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-primary">
              Create Session
            </button>
          </form>

          <div className="session-list">
            <h2>Active Sessions</h2>
           {sessions.map(session => {
  const start = new Date(session.startTime); // Parse start time
  const end = new Date(start.getTime() + session.duration * 60000); // Calculate end time

  return (
    <div key={session.id} className="session-card">
      <h3>{session.className}</h3>
      <p>Start: {start.toLocaleString()}</p>
      <p>End: {end.toLocaleString()}</p>
      <p>Location: {session.location.lat}, {session.location.lng} (Radius: {session.location.radius}m)</p>
      <div className="session-link">
        <span>Attendance Link: </span>
        <input 
          type="text" 
          value={`${window.location.origin}/session/${session.id}/attendance`}
          readOnly
        />
        <button 
          onClick={() => handleCopyLink(`${window.location.origin}/session/${session.id}/attendance`)}
          className="btn-secondary"
        >
          Copy Link
        </button>
      </div>
      <button 
        onClick={() => deleteSession(session.id)} 
        className="btn-danger"
      >
        Delete Session
      </button>
    </div>
  );
})}
          </div>

          <div className="attendance-records">
            <h2>Attendance Records</h2>
            <div className="controls">
              <select 
                value={selectedSession} 
                onChange={(e) => setSelectedSession(e.target.value)}
                className="session-selector"
              >
                <option value="all">All Sessions</option>
                {sessions.map(session => (
                  <option key={session.id} value={session.id}>
                    {session.className}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="records-table">
              {filteredAttendance.length === 0 ? (
                <p className="no-records">No attendance records yet</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Session</th>
                      <th>Time</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAttendance.map(entry => (
                      <tr key={entry.id}>
                        <td>{entry.name}</td>
                        <td>{sessionMap[entry.sessionId]?.className || 'Unknown Session'}</td>
                        <td>{entry.time}</td>
                        <td>
                          <button 
                            onClick={() => deleteRecord(entry.id)}
                            className="btn-danger"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [theme, setTheme] = useState('light');
  const [sessions, setSessions] = useState([]);
  const [attendance, setAttendance] = useState([]);

  useEffect(() => {
    const savedSessions = sessionStorage.getItem('sessions');
    const savedAttendance = sessionStorage.getItem('attendance');
    if (savedSessions) setSessions(JSON.parse(savedSessions));
    if (savedAttendance) setAttendance(JSON.parse(savedAttendance));
  }, []);

  useEffect(() => {
    sessionStorage.setItem('sessions', JSON.stringify(sessions));
    sessionStorage.setItem('attendance', JSON.stringify(attendance));
  }, [sessions, attendance]);

  const createSession = (sessionData) => {
    const newSession = {
      id: Date.now().toString(),
      className: sessionData.className,
      startTime: new Date(sessionData.startTime).toISOString(), // Store as ISO string
      duration: parseInt(sessionData.duration),
      location: {
        lat: parseFloat(sessionData.location.lat),
        lng: parseFloat(sessionData.location.lng),
        radius: parseInt(sessionData.location.radius)
      }
    };
    setSessions([...sessions, newSession]);
  };

  const deleteSession = (sessionId) => {
    setSessions(sessions.filter(s => s.id !== sessionId));
  };

  const markAttendance = (name, sessionId) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return false;
  
    const now = new Date(); // Current time
    const start = new Date(session.startTime); // Parse start time
    const end = new Date(start.getTime() + session.duration * 60000); // Calculate end time
  
    // Check if the current time is within the session's start and end times
    if (now < start || now > end) {
      return false; // Session is not active
    }
  
    // Check if the student has already marked attendance
    const existingEntry = attendance.find(entry => 
      entry.name === name && entry.sessionId === sessionId
    );
  
    if (existingEntry) return false; // Attendance already marked
  
    // Add new attendance record
    const newEntry = {
      id: Date.now(),
      name,
      sessionId,
      time: new Date().toLocaleString()
    };
    setAttendance([...attendance, newEntry]);
    return true;
  };
  const deleteRecord = (id) => {
    setAttendance(attendance.filter(entry => entry.id !== id));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme(t => t === 'light' ? 'dark' : 'light') }}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<IndexPage />} />
            <Route 
              path="/session/:sessionId/attendance" 
              element={<Student markAttendance={markAttendance} sessions={sessions} />} 
            />
            <Route 
              path="/teacher" 
              element={
                <Teacher 
                  sessions={sessions}
                  createSession={createSession}
                  attendance={attendance} 
                  deleteSession={deleteSession}
                  deleteRecord={deleteRecord}
                  logout={() => window.location.reload()}
                />
              } 
            />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeContext.Provider>
  );
}

export default App;