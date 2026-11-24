import sqlite3
import random
import string
from datetime import datetime

DB_NAME = "deskbridge.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Creates the users and tickets tables and seeds default demo accounts."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Dual-Account Users Table (Client vs IT Team)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('client', 'it_team')),
            full_name TEXT NOT NULL,
            department_or_org TEXT NOT NULL
        )
    """)

    # 2. Tickets Table (Stores diagnostics, ITIL tags, support choice, and escalation tier)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            client_username TEXT NOT NULL,
            hostname TEXT NOT NULL,
            error_code TEXT NOT NULL,
            itil_category TEXT NOT NULL,
            priority TEXT NOT NULL,
            technical_summary TEXT NOT NULL,
            ai_plain_explanation TEXT NOT NULL,
            support_mode TEXT NOT NULL,
            remote_consent_pin TEXT,
            status TEXT NOT NULL,
            assigned_tier TEXT NOT NULL,
            tech_notes TEXT
        )
    """)

    # Seed default accounts for instant testing
    default_users = [
        ("client1", "pass123", "client", "Thato Dintso", "Finance Dept"),
        ("tech1", "admin123", "it_team", "Naledi Khumalo", "Internal IT - Tier 1"),
        ("msp_tech", "msp123", "it_team", "Sipho Mokoena", "Apex IT Solutions (Outsourced MSP)")
    ]
    for user in default_users:
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role, full_name, department_or_org)
            VALUES (?, ?, ?, ?, ?)
        """, user)

    conn.commit()
    conn.close()


def authenticate_user(username, password):
    """Verifies login credentials and returns user profile (role: client or it_team)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username.strip(), password.strip())
    )
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def generate_ai_plain_explanation(error_code, technical_summary):
    """
    Translates specialized diagnostic codes into plain, actionable IT insights.
    (Structured so an external LLM API key can also be plugged in seamlessly.)
    """
    knowledge_base = {
        "NET-CONN-101": (
            "AI Root-Cause Insight: The client machine has lost Layer-3 outbound connectivity. "
            "Likely caused by a disconnected Wi-Fi adapter, disabled network interface, or upstream ISP/router drop. "
            "Recommended IT Action: Verify local gateway ping, check DHCP lease status, and inspect switch/router port."
        ),
        "NET-DNS-204": (
            "AI Root-Cause Insight: Raw IP traffic reaches external servers (8.8.8.8), but DNS resolution is failing. "
            "Likely caused by a corrupted local DNS resolver cache, VPN split-tunnel conflict, or unreachable DNS server. "
            "Recommended IT Action: Flush DNS cache, inspect network adapter DNS settings (ipconfig /all), or test alternate DNS."
        ),
        "HW-DISK-305": (
            "AI Root-Cause Insight: Primary OS partition has fallen below 10% free capacity, risking system instability "
            "and Windows Update failures. Recommended IT Action: Run disk cleanup, audit large temp/log files, or provision storage."
        ),
        "PERF-RAM-402": (
            "AI Root-Cause Insight: Physical memory saturation (>90%) is causing heavy page-file swapping and UI lag. "
            "Recommended IT Action: Identify memory-leaking processes via Task Manager/Resource Monitor and optimize startup apps."
        ),
        "SYS-OK-000": (
            "AI Root-Cause Insight: Core network, DNS, RAM, and storage telemetry are within normal thresholds. "
            "Fault is likely isolated to a specific application, user permissions, or peripheral device."
        )
    }
    return knowledge_base.get(
        error_code,
        f"AI Root-Cause Insight: Unmapped diagnostic event ({error_code}). Review raw telemetry: {technical_summary}"
    )


def create_ticket(client_username, diag_report, support_mode):
    """Logs a new ticket into SQLite with ITIL mapping, consent PIN (if granted), and AI summary."""
    conn = get_connection()
    cursor = conn.cursor()

    ticket_id = f"DB-{random.randint(1000, 9999)}"
    diag = diag_report["diagnosis"]
    error_code = diag["error_code"]
    tech_summary = diag["summary"]
    ai_explanation = generate_ai_plain_explanation(error_code, tech_summary)

    # Generate a 6-digit consent PIN ONLY if the client explicitly authorizes remote access
    remote_pin = None
    if support_mode == "Remote Access (Authorized)":
        remote_pin = "".join(random.choices(string.digits, k=6))

    status = "Resolved (Self-Service)" if support_mode == "Self-Troubleshoot" else "Open"
    resolved_at = diag_report["timestamp"] if status == "Resolved (Self-Service)" else None

    cursor.execute("""
        INSERT INTO tickets (
            ticket_id, created_at, resolved_at, client_username, hostname,
            error_code, itil_category, priority, technical_summary,
            ai_plain_explanation, support_mode, remote_consent_pin,
            status, assigned_tier, tech_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        diag_report["timestamp"],
        resolved_at,
        client_username,
        diag_report["hostname"],
        error_code,
        diag["itil_category"],
        diag["priority"],
        tech_summary,
        ai_explanation,
        support_mode,
        remote_pin,
        status,
        "Tier 1 - Service Desk",
        ""
    ))

    conn.commit()
    conn.close()
    return ticket_id, remote_pin


def get_all_tickets():
    """Fetches all tickets ordered by newest first for the IT Team dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def escalate_ticket(ticket_id, notes=""):
    """Escalates a ticket from Tier 1 to Tier 2 Specialist Support."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets
        SET assigned_tier = 'Tier 2 - Specialist Engineering',
            status = 'Escalated',
            tech_notes = ?
        WHERE ticket_id = ?
    """, (notes, ticket_id))
    conn.commit()
    conn.close()


def resolve_ticket(ticket_id, notes=""):
    """Marks a ticket as resolved with a timestamp for analytics tracking."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE tickets
        SET status = 'Resolved',
            resolved_at = ?,
            tech_notes = ?
        WHERE ticket_id = ?
    """, (now, notes, ticket_id))
    conn.commit()
    conn.close()


# Standalone test to initialize DB and verify ticket creation + escalation
if __name__ == "__main__":
    from diagnostics import run_system_diagnostics

    print("Initializing DeskBridge Database...")
    init_db()

    user = authenticate_user("client1", "pass123")
    print(f"Authenticated User: {user['full_name']} | Role: {user['role']} ({user['department_or_org']})")

    report = run_system_diagnostics()
    t_id, pin = create_ticket(user["username"], report, "Remote Access (Authorized)")
    print(f"Created Ticket: {t_id} | Remote Consent PIN: {pin}")

    tickets = get_all_tickets()
    print(f"Total Tickets in DB: {len(tickets)}")
    print(f"AI Translation for IT Team:\n  {tickets[0]['ai_plain_explanation']}")
