# AI-Powered Appointment Booking Assistant

Chat-based appointment booking system built with Streamlit, SQLite, and an AI extraction layer. Clients can book appointments using natural language or a manual form, reschedule or delete their bookings, and track booking status. Admin users can view, create, update, delete, filter, export, and manage the status of all bookings.

## Part 1: Problem Understanding

Appointment scheduling is frustrating. Users navigate complex forms, and service providers manage bookings manually. This project solves this by letting users book appointments using natural language instead of filling out tedious forms.

### The Problem: Traditional booking systems are time-consuming and error-prone. Users struggle with forms, and admins waste time managing scattered appointment data.

### The Solution: Our AI-powered system lets users book appointments conversationally. Simply type "I need a haircut on May 25th at 3 PM for John," and the AI extracts the details automatically and books it.

Who Uses It: There are two user types. Regular users can quickly book, view, and delete their own appointments. Admins have a comprehensive dashboard to manage all bookings, view statistics, search and filter by service, and export data to CSV.

Key Workflows: Users enter appointment requests in natural language, the AI processes and books it, then users can view or delete bookings anytime. Admins log in with a password to access a dashboard showing all bookings, statistics with charts, and management tools.

Why It Matters: Natural language removes friction from scheduling. Users don't memorize forms—they simply describe what they need. This makes booking accessible, reduces errors, and saves time for everyone.

## Part 2: Spec & Plan - 

### 1. System Design - High-Level

The application has two authenticated roles:

- Client: can create appointments and view, reschedule, or delete only their own bookings.
- Admin: can view all bookings from all users, perform CRUD operations, and update booking status.

High-level components:

- Streamlit UI: renders sign in/sign up, client booking screens, and admin dashboard.
- Authentication layer: stores users with hashed passwords and role-based access.
- SQLite database: stores users and appointments.
- AI handler: extracts appointment details from natural language booking requests.
- Availability checker: prevents duplicate active bookings for the same date and time.
- Admin management tools: allow filtering, editing, deleting, creating, status updates, and exporting bookings.

### 2. Feature Breakdown

- Client sign up and sign in
- Admin sign in
- Role-based authorization
- AI-based appointment creation from natural language
- Manual appointment creation
- Client-side booking list
- Client-side booking delete
- Client-side booking reschedule
- Booking status: `Pending`, `Confirmed`, `Cancelled`, `Completed`
- Availability checking to prevent duplicate active slots
- Sidebar counts for total and active bookings
- Admin dashboard statistics
- Admin all-bookings table with search, service filter, and status filter
- Admin create, update, delete operations
- Admin status management
- User list for admin
- CSV export for bookings

### 3. Prompt Design

The AI prompt asks the model to extract appointment details from user text and return only valid JSON with these fields:

```json
{
  "name": "John Doe",
  "service": "Haircut",
  "date": "May 25, 2026",
  "time": "3:00 PM"
}
```

Prompt goals:

- Keep output machine-readable.
- Require exact fields: `name`, `service`, `date`, and `time`.
- Use `"Not specified"` if a field is missing.
- Avoid extra explanation outside JSON.

### 4. Data Model

`users`

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER | Primary key |
| name | TEXT | User display name |
| email | TEXT | Unique login email |
| password_hash | TEXT | Salted password hash |
| role | TEXT | `client` or `admin` |
| created_at | TIMESTAMP | Account creation time |

`appointments`

| Field | Type | Description |
| --- | --- | --- |
| id | INTEGER | Primary key |
| user_id | INTEGER | Owner user ID for client bookings |
| name | TEXT | Client name |
| service | TEXT | Appointment service |
| date | TEXT | Appointment date |
| time | TEXT | Appointment time |
| status | TEXT | Booking status |
| created_at | TIMESTAMP | Booking creation time |

### 5. Implementation Plan

1. Build SQLite database helpers for users and appointments.
2. Add authentication with password hashing.
3. Seed demo client and admin accounts.
4. Build centered sign in/sign up UI.
5. Add role-based routing for client and admin.
6. Implement natural language booking extraction.
7. Add client booking creation and personal booking list.
8. Add client delete with ownership check.
9. Add booking status and active booking counts.
10. Add availability checks for booking creation and rescheduling.
11. Build admin dashboard with CRUD and status operations.
12. Add sidebar metrics and booking export.
13. Test client and admin flows.

## Part 3: Implementation - AI-Assisted

### Tech Stack

- Python
- Streamlit
- SQLite
- Pandas
- Groq API for AI extraction
- python-dotenv for environment variables

### AI Tools and Models Used

Coding assistant:

- Codex was used to help implement and refine the application.

Application AI model:

- The app uses Groq chat completions through `ai_handler.py`.
- The code tries several Groq models in order and selects the first available chat model.
- The model is used only to extract appointment details from natural language text into JSON.

Reason for choosing this approach:

- Streamlit makes it fast to build both client and admin interfaces.
- SQLite is simple and enough for a local assignment project.
- Groq chat models are suitable for quick structured extraction from natural language.
- Role-based login keeps client and admin flows separate.
- Booking status and availability checks make the workflow closer to a real appointment system.

Tokens used:

- 110k tokens used in codex.

### How to Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
ADMIN_NAME=Admin
```

4. Run the app:

```bash
streamlit run app.py
```

### Demo Accounts

Client:

- Email: `client@example.com`
- Password: `client123`

Admin:

- Email: `admin@example.com`
- Password: `admin123`

## Part 4: Edge Cases

- Missing booking details in natural language input
- Invalid AI response or non-JSON model output
- Empty manual booking form
- Duplicate signup email
- Wrong password during login
- Client attempting to access admin functionality
- Client attempting to delete another user's booking
- Client attempting to reschedule another user's booking
- Client attempting to book or reschedule into an occupied active slot
- Admin attempting to update a booking into an occupied active slot
- Cancelled or completed bookings not counted as active
- Admin deleting a booking that no longer exists
- Admin changing booking status between pending, confirmed, cancelled, and completed
- Unparseable date values when calculating active bookings
- No bookings available in client or admin views
- Empty search/filter results in admin dashboard
- Missing `GROQ_API_KEY` in `.env`

Suggested flow:

1. Show sign in/sign up page.
2. Sign in as client.
3. Create a booking using natural language.
4. Show total and active booking counts in sidebar.
5. Open My Bookings, reschedule a booking, and delete a booking.
6. Sign out and sign in as admin.
7. Show all bookings, statistics, status filter, and CRUD controls.
8. Explain the database, authentication, and AI extraction briefly.
