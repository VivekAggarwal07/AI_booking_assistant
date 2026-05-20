import json
import re
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from ai_handler import extract_booking_details
from database import (
    authenticate_user,
    create_user,
    delete_appointment,
    delete_appointment_for_user,
    fetch_appointments,
    fetch_appointments_by_user_id,
    fetch_users,
    get_appointment,
    insert_appointment,
    is_slot_available,
    update_appointment,
    update_appointment_for_user,
)

st.set_page_config(
    page_title="AI Booking Assistant",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { padding-top: 2rem; }
    .stButton > button {
        width: 100%;
        padding: 0.7rem;
        border-radius: 0.45rem;
        font-weight: 700;
    }
    .primary-card {
        border: 1px solid #d8dee8;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        background: #ffffff;
        margin-bottom: 1rem;
    }
    .metric-card {
        border: 1px solid #e4e7ec;
        border-radius: 8px;
        padding: 1rem;
        background: #f8fafc;
    }
    .metric-number {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1d4ed8;
    }
    .metric-label {
        color: #475569;
        font-size: 0.9rem;
    }
    .auth-heading {
        text-align: center;
        margin: 2rem 0 1.25rem;
    }
    .auth-heading h1 {
        margin-bottom: 0.25rem;
        font-size: 2rem;
    }
    .auth-heading p {
        color: #64748b;
        margin: 0;
    }
    .demo-box {
        border: 1px solid #dbeafe;
        border-radius: 8px;
        background: #eff6ff;
        padding: 0.8rem 1rem;
        margin: 0.75rem 0 1rem;
        color: #1e3a8a;
        font-size: 0.92rem;
    }
    .booking-list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: 0.25rem 0 1rem;
    }
    .booking-list-header h3 {
        margin: 0;
    }
    .booking-count-pill {
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        font-weight: 700;
        padding: 0.3rem 0.75rem;
        white-space: nowrap;
    }
    .booking-row {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: #ffffff;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .booking-row-top {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }
    .booking-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
    }
    .booking-id {
        color: #64748b;
        font-size: 0.9rem;
    }
    .booking-meta {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
    }
    .booking-meta-item {
        border: 1px solid #f1f5f9;
        border-radius: 8px;
        background: #f8fafc;
        padding: 0.65rem;
    }
    .booking-meta-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .booking-meta-value {
        color: #0f172a;
        font-weight: 700;
        margin-top: 0.15rem;
        overflow-wrap: anywhere;
    }
    @media (max-width: 760px) {
        .booking-meta { grid-template-columns: 1fr; }
        .booking-list-header { align-items: flex-start; flex-direction: column; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

LOGIN_MOCKS = {
    "client": {
        "label": "Client",
        "email": "client@example.com",
        "password": "client123",
        "description": "Client demo can create bookings and only view bookings from its own account.",
    },
    "admin": {
        "label": "Admin",
        "email": "admin@example.com",
        "password": "admin123",
        "description": "Admin demo can view all bookings and use create, update, delete, export, and users tools.",
    },
}

BOOKING_STATUSES = ["Pending", "Confirmed", "Cancelled", "Completed"]


def init_state():
    defaults = {
        "current_user": None,
        "active_side": "Client",
        "booking_processed": False,
        "booking_flash": None,
        "delete_flash": None,
        "reschedule_flash": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def required(value):
    return bool(str(value or "").strip())


def is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email or "").strip()))


def is_admin():
    user = st.session_state.current_user
    return bool(user and user["role"] == "admin")


def appointments_to_df(appointments):
    return pd.DataFrame(appointments, columns=["ID", "Name", "Service", "Date", "Time", "Status"])


def is_active_appointment(appointment):
    appointment_date = str(appointment[3] or "").strip()
    appointment_status = str(appointment[5] if len(appointment) > 5 else "Pending")
    if appointment_status in {"Cancelled", "Completed"}:
        return False

    if not appointment_date:
        return True

    parsed_date = pd.to_datetime(appointment_date, errors="coerce")
    if pd.isna(parsed_date):
        return True

    return parsed_date.date() >= date.today()


def count_active_appointments(appointments):
    return sum(1 for appointment in appointments if is_active_appointment(appointment))


def render_metric(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-number">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_booking_card(appointment):
    appointment_id, name, service, date, time, status = appointment
    st.markdown(
        f"""
        <div class="booking-row">
            <div class="booking-row-top">
                <div>
                    <div class="booking-title">{service}</div>
                    <div class="booking-id">Booking #{appointment_id}</div>
                </div>
                <div class="booking-count-pill">{status}</div>
            </div>
            <div class="booking-meta">
                <div class="booking-meta-item">
                    <div class="booking-meta-label">Client</div>
                    <div class="booking-meta-value">{name}</div>
                </div>
                <div class="booking-meta-item">
                    <div class="booking-meta-label">Date</div>
                    <div class="booking-meta-value">{date}</div>
                </div>
                <div class="booking-meta-item">
                    <div class="booking-meta-label">Time</div>
                    <div class="booking-meta-value">{time}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_booking_flash():
    flash = st.session_state.get("booking_flash")
    if not flash:
        return

    st.success(f"Booking #{flash['id']} created.")
    st.info(f"{flash['name']} is booked for {flash['service']} on {flash['date']} at {flash['time']}.")
    st.session_state.booking_flash = None


def set_booking_flash(appointment_id, name, service, date, time):
    st.session_state.booking_flash = {
        "id": appointment_id,
        "name": name,
        "service": service,
        "date": date,
        "time": time,
    }


def show_delete_flash():
    flash = st.session_state.get("delete_flash")
    if not flash:
        return

    if flash["deleted"]:
        st.success(f"Booking #{flash['id']} deleted.")
    else:
        st.error("This booking could not be deleted.")
    st.session_state.delete_flash = None


def delete_client_booking(appointment_id, user_id):
    deleted = delete_appointment_for_user(appointment_id, user_id)
    st.session_state.delete_flash = {
        "id": appointment_id,
        "deleted": bool(deleted),
    }


def show_reschedule_flash():
    flash = st.session_state.get("reschedule_flash")
    if not flash:
        return

    if flash["updated"]:
        st.success(f"Booking #{flash['id']} rescheduled and marked Pending.")
    else:
        st.error(flash["message"])
    st.session_state.reschedule_flash = None


def reschedule_client_booking(appointment_id, user_id, new_date, new_time):
    clean_date = str(new_date or "").strip()
    clean_time = str(new_time or "").strip()

    if not clean_date or not clean_time:
        st.session_state.reschedule_flash = {
            "id": appointment_id,
            "updated": False,
            "message": "Please enter both date and time to reschedule.",
        }
        return

    if not is_slot_available(clean_date, clean_time, exclude_appointment_id=appointment_id):
        st.session_state.reschedule_flash = {
            "id": appointment_id,
            "updated": False,
            "message": "That date and time is already booked. Please choose another slot.",
        }
        return

    updated = update_appointment_for_user(appointment_id, user_id, clean_date, clean_time)
    st.session_state.reschedule_flash = {
        "id": appointment_id,
        "updated": bool(updated),
        "message": "This booking could not be rescheduled.",
    }


def render_auth_page():
    left, center, right = st.columns([1, 1.15, 1])

    with center:
        st.markdown(
            """
            <div class="auth-heading">
                <h1>AI Booking Assistant</h1>
                <p>Sign in or create a client account to continue.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        signin_tab, signup_tab = st.tabs(["Sign in", "Sign up"])

        with signin_tab:
            selected_role_label = st.radio(
                "Login as",
                ["Client", "Admin"],
                horizontal=True,
                label_visibility="collapsed",
                key="login_role_toggle",
            )
            selected_role = selected_role_label.lower()
            mock = LOGIN_MOCKS[selected_role]

            st.markdown(
                f"""
                <div class="demo-box">
                    <strong>{mock["label"]} mock account</strong><br>
                    Email: {mock["email"]}<br>
                    Password: {mock["password"]}<br>
                    {mock["description"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form(f"signin_form_{selected_role}"):
                email = st.text_input("Email", value=mock["email"], key=f"signin_email_{selected_role}")
                password = st.text_input(
                    "Password",
                    value=mock["password"],
                    type="password",
                    key=f"signin_password_{selected_role}",
                )
                submitted = st.form_submit_button(f"Sign in as {mock['label']}", type="primary")

            if submitted:
                user = authenticate_user(email, password)
                if not user:
                    st.error("Invalid email or password.")
                elif user["role"] != selected_role:
                    st.error(f"This account is not authorized for {mock['label']} login.")
                else:
                    st.session_state.current_user = user
                    st.session_state.active_side = "Admin" if user["role"] == "admin" else "Client"
                    st.success("Signed in successfully.")
                    st.rerun()
                    return True

        with signup_tab:
            st.info("New signups are created as client accounts.")
            with st.form("signup_form"):
                name = st.text_input("Full name")
                email = st.text_input("Email address")
                password = st.text_input("Create password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create client account")

            if submitted:
                if not all(required(value) for value in [name, email, password, confirm_password]):
                    st.warning("Please fill in all fields.")
                elif not is_valid_email(email):
                    st.warning("Please enter a valid email address.")
                elif len(password) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif password != confirm_password:
                    st.warning("Passwords do not match.")
                else:
                    user_id = create_user(name, email, password, role="client")
                    if not user_id:
                        st.error("An account with this email already exists.")
                    else:
                        st.success("Account created. You can sign in from the Client toggle now.")

    return False


def sidebar():
    user = st.session_state.current_user
    with st.sidebar:
        st.header("Account")
        st.write(f"**{user['name']}**")
        st.caption(f"{user['email']} · {user['role'].title()}")

        if st.button("Sign out"):
            st.session_state.current_user = None
            st.session_state.active_side = "Client"
            st.rerun()

        st.divider()
        if is_admin():
            all_appointments = fetch_appointments()
            st.metric("Total bookings", len(all_appointments))
            st.metric("Active bookings", count_active_appointments(all_appointments))
        else:
            my_appointments = fetch_appointments_by_user_id(user["id"])
            st.metric("Total bookings", len(my_appointments))
            st.metric("Active bookings", count_active_appointments(my_appointments))


def create_manual_booking(name, service, date, time, user_id=None, status="Pending", flash=True):
    if not all(required(value) for value in [name, service, date, time]):
        st.warning("Please fill in name, service, date, and time.")
        return None

    clean_name = name.strip()
    clean_service = service.strip()
    clean_date = date.strip()
    clean_time = time.strip()

    if status not in {"Cancelled", "Completed"} and not is_slot_available(clean_date, clean_time):
        st.warning("That date and time is already booked. Please choose another slot.")
        return None

    appointment_id = insert_appointment(
        clean_name,
        clean_service,
        clean_date,
        clean_time,
        user_id=user_id,
        status=status,
    )
    if flash:
        set_booking_flash(appointment_id, clean_name, clean_service, clean_date, clean_time)
    return appointment_id


def process_ai_booking(user_input, user):
    if not required(user_input):
        st.warning("Please describe the appointment first.")
        return

    with st.spinner("Extracting booking details..."):
        try:
            result = extract_booking_details(user_input)
            appointment_data = json.loads(result)
        except json.JSONDecodeError:
            st.error("The AI response was not valid JSON. Try writing the request more directly.")
            st.code(result if "result" in locals() else "", language="text")
            return
        except Exception as exc:
            st.error(f"Could not process the booking: {exc}")
            return

    name = appointment_data.get("name", "").strip()
    service = appointment_data.get("service", "").strip()
    date = appointment_data.get("date", "").strip()
    time = appointment_data.get("time", "").strip()

    if name.lower() in {"", "not specified", "n/a"}:
        name = user["name"]

    if not all(required(value) for value in [name, service, date, time]):
        st.warning("I could not find all required details. Please include name, service, date, and time.")
        st.json(appointment_data)
        return

    if not is_slot_available(date, time):
        st.warning("That date and time is already booked. Please choose another slot.")
        return

    appointment_id = insert_appointment(name, service, date, time, user_id=user["id"])
    st.session_state.booking_processed = True
    set_booking_flash(appointment_id, name, service, date, time)


def render_client_side():
    user = st.session_state.current_user
    st.title("AI Appointment Booking Assistant")
    st.caption("Client side")
    show_booking_flash()
    show_delete_flash()
    show_reschedule_flash()

    tab_new, tab_mine = st.tabs(["New Booking", "My Bookings"])

    with tab_new:
        st.subheader("Book with AI")
        with st.form("ai_booking_form"):
            user_input = st.text_area(
                "Appointment request",
                height=130,
                placeholder="Example: Book a haircut on May 25 at 3 PM.",
            )
            book_submitted = st.form_submit_button("Book appointment", type="primary")
            if book_submitted:
                process_ai_booking(user_input, user)
                show_booking_flash()

        st.divider()
        st.subheader("Manual booking")
        with st.form("client_manual_booking", clear_on_submit=True):
            name = st.text_input("Name", value=user["name"])
            service = st.text_input("Service")
            date = st.text_input("Date")
            time = st.text_input("Time")
            submitted = st.form_submit_button("Save booking")

        if submitted:
            appointment_id = create_manual_booking(name, service, date, time, user_id=user["id"])
            if appointment_id:
                show_booking_flash()

    with tab_mine:
        appointments = fetch_appointments_by_user_id(user["id"])

        if not appointments:
            st.markdown(
                """
                <div class="booking-list-header">
                    <h3>My Appointments</h3>
                    <span class="booking-count-pill">0 bookings</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info("No bookings found for your account.")
            return

        active_count = count_active_appointments(appointments)
        st.markdown(
            f"""
            <div class="booking-list-header">
                <h3>My Appointments</h3>
                <span class="booking-count-pill">{len(appointments)} total · {active_count} active</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for appointment in appointments:
            appointment_id, _, _, current_date, current_time, status = appointment
            details_col, action_col = st.columns([5, 1])
            with details_col:
                render_booking_card(appointment)
            with action_col:
                st.button(
                    "Delete",
                    key=f"client_delete_{appointment_id}",
                    type="secondary",
                    use_container_width=True,
                    on_click=delete_client_booking,
                    args=(appointment_id, user["id"]),
                )
            if status not in {"Cancelled", "Completed"}:
                with st.expander(f"Reschedule booking #{appointment_id}"):
                    with st.form(f"client_reschedule_{appointment_id}"):
                        new_date = st.text_input("New date", value=current_date)
                        new_time = st.text_input("New time", value=current_time)
                        submitted = st.form_submit_button("Reschedule")

                    if submitted:
                        reschedule_client_booking(appointment_id, user["id"], new_date, new_time)
                        show_reschedule_flash()


def render_admin_stats(appointments):
    st.subheader("Dashboard")

    if not appointments:
        st.info("No bookings yet.")
        return

    df = appointments_to_df(appointments)
    col_total, col_active, col_services, col_clients = st.columns(4)
    with col_total:
        render_metric("Total bookings", len(df))
    with col_active:
        render_metric("Active bookings", count_active_appointments(appointments))
    with col_services:
        render_metric("Services", df["Service"].nunique())
    with col_clients:
        render_metric("Clients", df["Name"].nunique())

    st.markdown(f"**Top service:** {df['Service'].value_counts().idxmax()}")

    st.divider()
    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        st.subheader("Bookings by service")
        st.bar_chart(df["Service"].value_counts())
    with chart_col_2:
        st.subheader("Bookings by client")
        st.bar_chart(df["Name"].value_counts().head(10))


def render_admin_bookings(appointments):
    st.subheader("All Bookings")

    if not appointments:
        st.info("No appointments in the system.")
        return

    df = appointments_to_df(appointments)
    col_search, col_service, col_status = st.columns(3)
    with col_search:
        search = st.text_input("Search name or service")
    with col_service:
        service_options = ["All"] + sorted(df["Service"].dropna().unique().tolist())
        selected_service = st.selectbox("Filter service", service_options)
    with col_status:
        selected_status = st.selectbox("Filter status", ["All"] + BOOKING_STATUSES)

    filtered_df = df.copy()
    if required(search):
        filtered_df = filtered_df[
            filtered_df["Name"].str.contains(search, case=False, na=False)
            | filtered_df["Service"].str.contains(search, case=False, na=False)
        ]
    if selected_service != "All":
        filtered_df = filtered_df[filtered_df["Service"] == selected_service]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["Status"] == selected_status]

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        filtered_df.to_csv(index=False),
        file_name="bookings.csv",
        mime="text/csv",
        use_container_width=True,
    )


def user_picker():
    clients = fetch_users(role="client")
    if not clients:
        return None

    client_by_label = {
        f"{name} ({email})": {"id": user_id, "name": name, "email": email}
        for user_id, name, email, _ in clients
    }
    label = st.selectbox("Assign to client account", ["No account"] + list(client_by_label.keys()))
    return None if label == "No account" else client_by_label[label]


def render_admin_create():
    st.subheader("Create Booking")
    selected_user = user_picker()

    with st.form("admin_create_booking", clear_on_submit=True):
        name_default = selected_user["name"] if selected_user else ""
        name = st.text_input("Client name", value=name_default)
        service = st.text_input("Service")
        date = st.text_input("Date")
        time = st.text_input("Time")
        status = st.selectbox("Status", BOOKING_STATUSES, index=1)
        submitted = st.form_submit_button("Create booking")

    if submitted:
        user_id = selected_user["id"] if selected_user else None
        appointment_id = create_manual_booking(name, service, date, time, user_id=user_id, status=status, flash=False)
        if appointment_id:
            st.success(f"Booking #{appointment_id} created.")
            st.rerun()


def render_admin_update_delete(appointments):
    st.subheader("Update or Delete Booking")

    if not appointments:
        st.info("No bookings available to manage.")
        return

    df = appointments_to_df(appointments)
    selected_id = st.selectbox(
        "Select booking",
        df["ID"].tolist(),
        format_func=lambda appointment_id: (
            f"#{appointment_id} - "
            f"{df.loc[df['ID'] == appointment_id, 'Name'].iloc[0]} "
            f"({df.loc[df['ID'] == appointment_id, 'Service'].iloc[0]})"
        ),
    )

    selected = get_appointment(selected_id)
    if not selected:
        st.error("Selected booking was not found.")
        return

    _, current_name, current_service, current_date, current_time, current_status = selected

    with st.form(f"admin_update_booking_{selected_id}"):
        name = st.text_input("Client name", value=current_name)
        service = st.text_input("Service", value=current_service)
        date = st.text_input("Date", value=current_date)
        time = st.text_input("Time", value=current_time)
        status = st.selectbox(
            "Status",
            BOOKING_STATUSES,
            index=BOOKING_STATUSES.index(current_status) if current_status in BOOKING_STATUSES else 0,
        )
        save_changes = st.form_submit_button("Update booking")

    if save_changes:
        if not all(required(value) for value in [name, service, date, time]):
            st.warning("Please fill in name, service, date, and time.")
        elif status not in {"Cancelled", "Completed"} and not is_slot_available(date.strip(), time.strip(), exclude_appointment_id=selected_id):
            st.warning("That date and time is already booked. Please choose another slot.")
        else:
            updated = update_appointment(selected_id, name.strip(), service.strip(), date.strip(), time.strip(), status)
            if updated:
                st.success(f"Booking #{selected_id} updated.")
                st.rerun()
            else:
                st.error("No booking was updated.")

    st.divider()
    confirm_delete = st.checkbox(f"Confirm delete booking #{selected_id}")
    if st.button("Delete booking", type="secondary", disabled=not confirm_delete):
        deleted = delete_appointment(selected_id)
        if deleted:
            st.success(f"Booking #{selected_id} deleted.")
            st.rerun()
        else:
            st.error("No booking was deleted.")


def render_admin_users():
    st.subheader("Users")
    users = fetch_users()
    if not users:
        st.info("No users found.")
        return

    users_df = pd.DataFrame(users, columns=["ID", "Name", "Email", "Role"])
    st.dataframe(users_df, use_container_width=True, hide_index=True)


def render_admin_side():
    if not is_admin():
        st.error("You do not have permission to access the admin area.")
        return

    st.title("Admin Dashboard")
    st.caption("Admin side")

    st.button("Refresh data", help="Reloads data with Streamlit's normal refresh cycle.")

    appointments = fetch_appointments()
    tab_stats, tab_all, tab_create, tab_manage, tab_users = st.tabs(
        ["Statistics", "All Bookings", "Create", "Update / Delete", "Users"]
    )

    with tab_stats:
        render_admin_stats(appointments)
    with tab_all:
        render_admin_bookings(appointments)
    with tab_create:
        render_admin_create()
    with tab_manage:
        render_admin_update_delete(appointments)
    with tab_users:
        render_admin_users()


if not st.session_state.current_user:
    signed_in = render_auth_page()
    if not signed_in:
        st.stop()

if st.session_state.current_user:
    if is_admin():
        render_admin_side()
    else:
        render_client_side()
    sidebar()
