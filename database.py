import sqlite3
import os
import hashlib
import secrets

DB_PATH = "appointments.db"

def get_connection():
    """Create and return a database connection"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database with users and appointments tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'client',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        service TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("PRAGMA table_info(appointments)")
    appointment_columns = [column[1] for column in cursor.fetchall()]
    if "user_id" not in appointment_columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN user_id INTEGER")
    if "status" not in appointment_columns:
        cursor.execute("ALTER TABLE appointments ADD COLUMN status TEXT NOT NULL DEFAULT 'Pending'")

    seed_demo_accounts(cursor)
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Create a salted password hash."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """Verify a password against a salted hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)
    except ValueError:
        return False

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return secrets.compare_digest(password_hash, expected_hash)


def seed_demo_accounts(cursor):
    """Create demo client/admin accounts when they do not exist."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin")

    demo_users = [
        (admin_name, admin_email, admin_password, "admin"),
        ("Demo Client", "client@example.com", "client123", "client"),
    ]

    for name, email, password, role in demo_users:
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        if cursor.fetchone():
            continue

        cursor.execute(
            """
            INSERT INTO users(name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, hash_password(password), role),
        )


def create_user(name, email, password, role="client"):
    """Create a user account."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users(name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), email.strip().lower(), hash_password(password), role),
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(email, password):
    """Return a user when email and password are valid."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, email, password_hash, role
        FROM users
        WHERE LOWER(email) = LOWER(?)
        """,
        (email.strip().lower(),),
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    user_id, name, user_email, password_hash, role = user
    if not verify_password(password, password_hash):
        return None

    return {
        "id": user_id,
        "name": name,
        "email": user_email,
        "role": role,
    }


def fetch_users(role=None):
    """Fetch users, optionally filtered by role."""
    conn = get_connection()
    cursor = conn.cursor()

    if role:
        cursor.execute(
            "SELECT id, name, email, role FROM users WHERE role = ? ORDER BY name",
            (role,),
        )
    else:
        cursor.execute("SELECT id, name, email, role FROM users ORDER BY name")

    users = cursor.fetchall()
    conn.close()

    return users


def insert_appointment(name, service, date, time, user_id=None, status="Pending"):
    """Insert a new appointment into the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO appointments(user_id, name, service, date, time, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, service, date, time, status))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id


def fetch_appointments():
    """Fetch all appointments from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, service, date, time, status FROM appointments ORDER BY id DESC")
    
    appointments = cursor.fetchall()
    conn.close()
    
    return appointments


def fetch_appointments_by_user_id(user_id):
    """Fetch appointments owned by one user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, service, date, time, status
        FROM appointments
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    appointments = cursor.fetchall()
    conn.close()

    return appointments


def fetch_appointments_by_name(name):
    """Fetch appointments for one client name."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, service, date, time, status
        FROM appointments
        WHERE LOWER(name) = LOWER(?)
        ORDER BY id DESC
        """,
        (name.strip(),),
    )

    appointments = cursor.fetchall()
    conn.close()

    return appointments


def get_appointment(appointment_id):
    """Fetch one appointment by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, service, date, time, status FROM appointments WHERE id = ?",
        (appointment_id,),
    )

    appointment = cursor.fetchone()
    conn.close()

    return appointment


def update_appointment(appointment_id, name, service, date, time, status):
    """Update an appointment by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET name = ?, service = ?, date = ?, time = ?, status = ?
        WHERE id = ?
        """,
        (name, service, date, time, status, appointment_id),
    )

    updated_count = cursor.rowcount
    conn.commit()
    conn.close()

    return updated_count


def update_appointment_for_user(appointment_id, user_id, date, time):
    """Reschedule a user's own appointment and return the updated row count."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET date = ?, time = ?, status = 'Pending'
        WHERE id = ? AND user_id = ?
        """,
        (date, time, appointment_id, user_id),
    )

    updated_count = cursor.rowcount
    conn.commit()
    conn.close()

    return updated_count


def is_slot_available(date, time, exclude_appointment_id=None):
    """Check if a date/time slot is free for active bookings."""
    conn = get_connection()
    cursor = conn.cursor()

    params = [date.strip().lower(), time.strip().lower()]
    query = """
        SELECT id
        FROM appointments
        WHERE LOWER(TRIM(date)) = ?
          AND LOWER(TRIM(time)) = ?
          AND status NOT IN ('Cancelled', 'Completed')
    """

    if exclude_appointment_id is not None:
        query += " AND id != ?"
        params.append(exclude_appointment_id)

    cursor.execute(query, params)
    conflict = cursor.fetchone()
    conn.close()

    return conflict is None


def delete_appointment(appointment_id):
    """Delete an appointment by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def delete_appointment_for_user(appointment_id, user_id):
    """Delete an appointment only when it belongs to the given user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM appointments WHERE id = ? AND user_id = ?",
        (appointment_id, user_id),
    )

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


# Initialize database on module import after all helpers are available.
init_db()
