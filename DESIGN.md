# AI Appointment Booking Assistant - High-Level Design

## 📋 Project Overview

A web-based appointment booking system that uses AI to extract booking details from natural language input. The system has two user roles with distinct workflows:
- **Users**: Book, view, and manage their own appointments
- **Admins**: Manage all bookings, view statistics, and export data

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                   │
│  ┌────────────────┐                ┌─────────────────┐  │
│  │  User Mode     │                │  Admin Mode     │  │
│  │  - New Booking │                │  - Statistics   │  │
│  │  - My Bookings │                │  - All Bookings │  │
│  │  - Delete      │                │  - Management   │  │
│  └────────────────┘                └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│            Authentication & Session Layer               │
│  - Password validation                                  │
│  - Admin password protection                            │
│  - Session state management                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Business Logic Layer                       │
│  ┌──────────────────┐     ┌──────────────────────────┐  │
│  │  AI Handler      │     │  Database Operations    │  │
│  │  - Extract JSON  │     │  - Insert appointment   │  │
│  │  - Parse text    │     │  - Fetch bookings       │  │
│  │  - Groq API      │     │  - Delete appointment   │  │
│  └──────────────────┘     └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Data Layer (SQLite)                        │
│  - appointments table (ID, Name, Service, Date, Time)  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Components

### 1. **Frontend (app.py)**
- **Streamlit Web Interface**
  - Responsive, multi-tab layout
  - Real-time state management
  - Sidebar with navigation and quick stats

#### User Mode
- **New Booking Tab**: Text input for AI extraction
- **My Bookings Tab**: Display user's appointments with delete button
- Quick stats: Total bookings, Active bookings

#### Admin Mode
- **Statistics Tab**: Dashboard with charts and metrics
- **All Bookings Tab**: Searchable table with filters
- **Management Tab**: Delete, export, manage bookings
- Refresh button for real-time data

### 2. **AI Handler (ai_handler.py)**
- **Groq API Integration**
  - Dynamic model selection (tries multiple models)
  - Fallback to available chat models
  
- **JSON Extraction**
  - Parses natural language input
  - Returns structured JSON: `{name, service, date, time}`
  - Handles markdown code blocks and explanatory text

- **Error Handling**
  - Graceful fallback for unavailable models
  - JSON parsing with robust extraction

### 3. **Database Layer (database.py)**
- **SQLite Connection Management**
  - Connection pooling
  - Transaction handling

- **Core Operations**
  - `insert_appointment()` - Add new booking
  - `fetch_appointments()` - Get all bookings
  - `delete_appointment()` - Remove booking

- **Schema**
  ```sql
  appointments(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    service TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```

### 4. **Environment Configuration (.env)**
```
GROQ_API_KEY=your_api_key
ADMIN_PASSWORD=admin123
```

---

## 🔄 User Flows

### User Booking Flow
```
1. User opens app → User Mode (default)
2. User enters appointment details in text
3. AI extracts: name, service, date, time
4. System saves to database
5. Booking appears in "My Bookings"
6. User can delete booking anytime
```

### Admin Access Flow
```
1. Admin enters admin password in sidebar
2. Unlock "⚙️ Admin" button
3. Switch to Admin Mode
4. View all bookings, stats, manage appointments
5. Click "🚪 Logout" to return to user mode
```

---

## 📊 Data Model

### Appointments Table
| Field | Type | Purpose |
|-------|------|---------|
| id | INTEGER | Unique booking ID |
| name | TEXT | Client name |
| service | TEXT | Service type (haircut, massage, etc.) |
| date | TEXT | Appointment date |
| time | TEXT | Appointment time |
| created_at | TIMESTAMP | When booking was made |

---

## 🎯 Features

### User Features
✅ AI-powered natural language booking  
✅ View personal bookings  
✅ Delete own bookings  
✅ Real-time booking updates  
✅ Quick stats sidebar  

### Admin Features
✅ View all user bookings  
✅ Search by name/service  
✅ Filter by service type  
✅ Delete any booking  
✅ Export to CSV  
✅ Dashboard statistics  
✅ Service breakdown charts  
✅ Top clients analysis  
✅ Password-protected access  

---

## 🛡️ Security & Authentication

- **Password Protection**: Admin mode requires password from `.env`
- **Session State**: Tracks login status using Streamlit session
- **No User Accounts**: Simplified auth (password-only for admin)
- **Environment Variables**: Sensitive data in `.env` (not committed)

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|------------|
| UI | Streamlit |
| Database | SQLite |
| AI | Groq API (LLaMA/Mixtral) |
| Language | Python 3 |
| Async | Streamlit built-in |
| Styling | CSS + Markdown |

---

## 📦 Dependencies

```
streamlit==1.28.0        # Web framework
groq>=0.9.0              # AI API client
python-dotenv==1.0.0     # Environment variables
pandas==2.0.0            # Data manipulation
```

---

## ⚙️ System Design Patterns

### 1. **Session State Management**
- Persistent across page reruns
- Tracks login status, booking state
- Prevents duplicate processing

### 2. **Component Reusability**
- `render_booking_card()` - Reused in user & admin modes
- `process_booking()` - Shared booking logic

### 3. **Error Handling**
- Graceful JSON parsing with extraction
- Model fallback strategy
- User-friendly error messages

### 4. **Real-Time Updates**
- `st.rerun()` after actions
- Sidebar refreshes stats on booking/delete

---

## 🔌 Integration Points

### Groq API
```python
client.chat.completions.create(
    model="llama-3.2-90b-text-preview",
    messages=[...],
    temperature=0.5
)
```

### SQLite
```python
cursor.execute("SELECT * FROM appointments")
conn.commit()
```

---

## 📈 Scalability Considerations

### Current Limitations
- Single-user admin (password-only, no user accounts)
- SQLite (no multi-instance support)
- No pagination (all bookings loaded at once)
- No caching

### Future Improvements
- PostgreSQL for production
- User authentication with roles
- Pagination for large datasets
- Caching layer
- API endpoints (FastAPI)
- Real-time notifications

---

## 🧪 Testing Scenarios

### Happy Path
1. Book appointment with AI
2. View in My Bookings
3. Delete booking
4. Login as admin
5. See all bookings, search, filter, export

### Edge Cases
- Empty booking inputs
- Invalid JSON responses
- Special characters in names
- Duplicate bookings
- Rapid add/delete operations
- Model unavailability fallback

---

## 📝 File Structure

```
AI_booking_assistant/
├── app.py                 # Main Streamlit app
├── ai_handler.py          # AI extraction logic
├── database.py            # SQLite operations
├── requirements.txt       # Dependencies
├── .env                   # Secrets (not committed)
├── appointments.db        # SQLite database
├── README.md              # Documentation
└── DESIGN.md              # This file
```

---

## 🚀 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env with secrets
echo "GROQ_API_KEY=your_key" > .env
echo "ADMIN_PASSWORD=admin123" >> .env

# Run app
streamlit run app.py
```

Then:
- Visit: `http://localhost:8501`
- Book appointment → View → Manage
- Admin password: `admin123`

---

## 📊 Quick Stats (Sidebar)

Real-time metrics:
- 📅 **Total Bookings**: Count of all appointments
- ⏳ **Active Bookings**: Currently pending bookings
- 🛠️ **Unique Services**: Number of service types

---

## 🎨 UI/UX Design Highlights

✨ **Clean, intuitive interface**  
✨ **Two-mode navigation** (User/Admin)  
✨ **Tab-based organization**  
✨ **Color-coded status** (success/error/info)  
✨ **Responsive cards** for bookings  
✨ **Real-time updates**  
✨ **Search & filter capabilities**  
✨ **Dark mode compatible**  

---

## 📞 Support & Maintenance

- Logs: Check Streamlit terminal output
- Database: Inspect `appointments.db` directly
- Errors: Check `.env` configuration
- Models: Groq automatically handles model switching

---

**Version**: 1.0  
**Last Updated**: May 2026  
**Author**: AI Booking Assistant Team
