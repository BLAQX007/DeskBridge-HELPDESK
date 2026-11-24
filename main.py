import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime

from diagnostics import run_system_diagnostics
from database import (
    init_db,
    authenticate_user,
    create_ticket,
    get_all_tickets,
    escalate_ticket,
    resolve_ticket,
)


class DeskBridgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeskBridge — Dual-Sided IT Support & Diagnostics")
        self.root.geometry("860x560")
        self.root.configure(bg="#12161f")
        self.current_user = None
        self.last_report = None

        init_db()
        self.setup_styles()
        self.show_login_screen()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#12161f")
        style.configure("Card.TFrame", background="#1c2230", relief="flat")
        style.configure("TLabel", background="#12161f", foreground="#e6edf3", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#1c2230", foreground="#e6edf3", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#12161f", foreground="#58a6ff", font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background="#12161f", foreground="#8b949e", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Treeview", background="#1c2230", foreground="#e6edf3", fieldbackground="#1c2230", rowheight=26)
        style.configure("Treeview.Heading", background="#262f42", foreground="#58a6ff", font=("Segoe UI", 9, "bold"))

    def clear_screen(self):
        self.root.unbind_all("<Control-period>")
        for widget in self.root.winfo_children():
            widget.destroy()

    # =========================================================================
    # 1. DUAL-ACCOUNT LOGIN SCREEN
    # =========================================================================
    def show_login_screen(self):
        self.clear_screen()
        container = ttk.Frame(self.root)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(container, text="DeskBridge", style="Header.TLabel").pack(pady=(0, 4))
        ttk.Label(
            container,
            text="Automated System Triage & Dual-Sided IT Help Desk",
            style="Sub.TLabel",
        ).pack(pady=(0, 20))

        card = ttk.Frame(container, style="Card.TFrame", padding=24)
        card.pack()

        ttk.Label(card, text="Username:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=6)
        self.user_entry = ttk.Entry(card, width=28, font=("Segoe UI", 10))
        self.user_entry.grid(row=0, column=1, pady=6, padx=(10, 0))
        self.user_entry.insert(0, "client1")

        ttk.Label(card, text="Password:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=6)
        self.pass_entry = ttk.Entry(card, width=28, show="*", font=("Segoe UI", 10))
        self.pass_entry.grid(row=1, column=1, pady=6, padx=(10, 0))
        self.pass_entry.insert(0, "pass123")

        ttk.Button(
            card, text="Sign In", style="Accent.TButton", command=self.handle_login
        ).grid(row=2, column=0, columnspan=2, pady=(16, 8), sticky="ew")

        demo_frame = ttk.Frame(container)
        demo_frame.pack(pady=(16, 0))
        ttk.Label(demo_frame, text="Quick Demo Fill:", style="Sub.TLabel").pack(side="left", padx=4)
        ttk.Button(
            demo_frame,
            text="Client Account",
            command=lambda: self.fill_demo("client1", "pass123"),
        ).pack(side="left", padx=4)
        ttk.Button(
            demo_frame,
            text="Internal IT Team",
            command=lambda: self.fill_demo("tech1", "admin123"),
        ).pack(side="left", padx=4)
        ttk.Button(
            demo_frame,
            text="Outsourced MSP",
            command=lambda: self.fill_demo("msp_tech", "msp123"),
        ).pack(side="left", padx=4)

    def fill_demo(self, username, password):
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, username)
        self.pass_entry.delete(0, tk.END)
        self.pass_entry.insert(0, password)

    def handle_login(self):
        user = authenticate_user(self.user_entry.get(), self.pass_entry.get())
        if not user:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return
        self.current_user = user
        if user["role"] == "client":
            self.show_client_dashboard()
        else:
            self.show_it_dashboard()

    # =========================================================================
    # 2. CLIENT ACCOUNT VIEW (HOTKEY Ctrl + . & SELF-TROUBLESHOOT / TICKETING)
    # =========================================================================
    def show_client_dashboard(self):
        self.clear_screen()
        self.root.bind_all("<Control-period>", lambda e: self.trigger_client_scan())

        top_bar = ttk.Frame(self.root, padding=(16, 12))
        top_bar.pack(fill="x")
        ttk.Label(
            top_bar,
            text=f"Client Portal — {self.current_user['full_name']} ({self.current_user['department_or_org']})",
            style="Header.TLabel",
        ).pack(side="left")
        ttk.Button(top_bar, text="Logout", command=self.show_login_screen).pack(side="right")

        banner = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        banner.pack(fill="x", padx=16, pady=6)
        ttk.Label(
            banner,
            text="Press  Ctrl + .  at any time (or click below) to run an instant automated system health scan.",
            style="Card.TLabel",
        ).pack(side="left")
        ttk.Button(
            banner,
            text="Run Diagnostic Scan (Ctrl + .)",
            style="Accent.TButton",
            command=self.trigger_client_scan,
        ).pack(side="right")

        self.diag_frame = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        self.diag_frame.pack(fill="both", expand=True, padx=16, pady=10)

        self.diag_output = tk.Text(
            self.diag_frame,
            height=13,
            bg="#0d1117",
            fg="#c9d1d9",
            font=("Consolas", 10),
            relief="flat",
            padx=12,
            pady=12,
        )
        self.diag_output.pack(fill="both", expand=True)
        self.diag_output.insert(
            "1.0",
            "System Ready.\nPress Ctrl + . whenever you experience network drops, slow performance, or system errors.",
        )
        self.diag_output.config(state="disabled")

        action_bar = ttk.Frame(self.root, padding=(16, 10))
        action_bar.pack(fill="x")

        ttk.Label(action_bar, text="Choose Support Option:").pack(side="left", padx=(0, 8))
        self.support_choice = tk.StringVar(value="Self-Troubleshoot")
        options = [
            "Self-Troubleshoot",
            "Remote Access (Authorized)",
            "Voice / Video Walkthrough",
            "Walk-In IT Support",
        ]
        ttk.Combobox(
            action_bar, textvariable=self.support_choice, values=options, state="readonly", width=28
        ).pack(side="left", padx=4)

        ttk.Button(
            action_bar,
            text="Submit / Log Ticket",
            style="Accent.TButton",
            command=self.submit_client_ticket,
        ).pack(side="right")

    def trigger_client_scan(self):
        self.diag_output.config(state="normal")
        self.diag_output.delete("1.0", tk.END)
        self.diag_output.insert("1.0", "Scanning network, DNS, memory, and storage... please wait...\n")
        self.root.update_idletasks()

        report = run_system_diagnostics()
        self.last_report = report
        diag = report["diagnosis"]
        tel = report["telemetry"]

        lines = [
            f"SCAN TIMESTAMP : {report['timestamp']}  |  HOST: {report['hostname']} ({report['os_info']})",
            f"TELEMETRY      : Internet={'OK' if tel['internet_connected'] else 'DOWN'} | "
            f"DNS={'OK' if tel['dns_working'] else 'FAIL'} | "
            f"Disk Free={tel['disk_free_percent']}% ({tel['disk_free_gb']} GB) | RAM Load={tel['ram_usage_percent']}%",
            "-" * 78,
            f"SPECIALIZED ERROR CODE : {diag['error_code']}",
            f"ITIL CATEGORY          : {diag['itil_category']}",
            f"ASSIGNED PRIORITY      : {diag['priority']}",
            f"DIAGNOSIS SUMMARY      : {diag['summary']}",
            "-" * 78,
            "RECOMMENDED TROUBLESHOOTING STEPS:",
        ]
        for step in diag["self_fix_steps"]:
            lines.append(f"  {step}")

        self.diag_output.delete("1.0", tk.END)
        self.diag_output.insert("1.0", "\n".join(lines))
        self.diag_output.config(state="disabled")

        if diag["can_self_fix"]:
            self.support_choice.set("Self-Troubleshoot")
        else:
            self.support_choice.set("Remote Access (Authorized)")

    def submit_client_ticket(self):
        if not self.last_report:
            messagebox.showwarning("Scan Required", "Please press Ctrl + . or run a diagnostic scan first.")
            return

        mode = self.support_choice.get()
        ticket_id, remote_pin = create_ticket(self.current_user["username"], self.last_report, mode)

        if mode == "Self-Troubleshoot":
            messagebox.showinfo(
                "Self-Service Logged",
                f"Ticket {ticket_id} logged as Self-Service Resolved!\n\n"
                "If the troubleshooting steps didn't fix the problem, run a scan again and select an IT support option.",
            )
        elif mode == "Remote Access (Authorized)":
            messagebox.showinfo(
                "Remote Session Authorized",
                f"Ticket {ticket_id} sent to IT Support!\n\n"
                f"Your One-Time Remote Consent PIN is:  {remote_pin}\n"
                "Only share or keep this active while your IT technician assists you.",
            )
        else:
            messagebox.showinfo(
                "IT Support Ticket Logged",
                f"Ticket {ticket_id} has been dispatched to the IT Support queue.\n"
                f"Requested Mode: {mode}\n"
                f"Error Code: {self.last_report['diagnosis']['error_code']}",
            )

    # =========================================================================
    # 3. IT TEAM & MSP DASHBOARD (CODE TRANSLATOR, ESCALATION, & ANALYTICS)
    # =========================================================================
    def show_it_dashboard(self):
        self.clear_screen()
        top_bar = ttk.Frame(self.root, padding=(16, 10))
        top_bar.pack(fill="x")
        ttk.Label(
            top_bar,
            text=f"IT Operations Console — {self.current_user['full_name']} ({self.current_user['department_or_org']})",
            style="Header.TLabel",
        ).pack(side="left")
        ttk.Button(top_bar, text="Logout", command=self.show_login_screen).pack(side="right")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        queue_tab = ttk.Frame(notebook, padding=10)
        notebook.add(queue_tab, text="Ticket Queue & AI Code Decoder")

        cols = ("ID", "Host", "Error Code", "ITIL Category", "Priority", "Support Mode", "Tier", "Status")
        self.tree = ttk.Treeview(queue_tab, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=98, anchor="center")
        self.tree.pack(fill="x", pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_ticket_select)

        self.ai_box = tk.Text(
            queue_tab,
            height=7,
            bg="#0d1117",
            fg="#7ee787",
            font=("Consolas", 9),
            relief="flat",
            padx=10,
            pady=8,
        )
        self.ai_box.pack(fill="both", expand=True, pady=(0, 8))
        self.ai_box.insert("1.0", "Select a ticket above to decode its error code and view AI root-cause guidance.")
        self.ai_box.config(state="disabled")

        ctrl_frame = ttk.Frame(queue_tab)
        ctrl_frame.pack(fill="x")
        ttk.Label(ctrl_frame, text="Tech Notes:").pack(side="left", padx=(0, 6))
        self.notes_entry = ttk.Entry(ctrl_frame, width=32)
        self.notes_entry.pack(side="left", padx=(0, 10))

        ttk.Button(ctrl_frame, text="Refresh", command=self.load_tickets).pack(side="left", padx=3)
        ttk.Button(
            ctrl_frame, text="Escalate to Tier 2", command=self.handle_escalate
        ).pack(side="right", padx=3)
        ttk.Button(
            ctrl_frame, text="Mark Resolved", style="Accent.TButton", command=self.handle_resolve
        ).pack(side="right", padx=3)

        analytics_tab = ttk.Frame(notebook, padding=16)
        notebook.add(analytics_tab, text="Data & Reporting Insights")

        self.analytics_text = tk.Text(
            analytics_tab,
            height=15,
            bg="#0d1117",
            fg="#e6edf3",
            font=("Consolas", 10),
            relief="flat",
            padx=14,
            pady=14,
        )
        self.analytics_text.pack(fill="both", expand=True, pady=(0, 10))

        btn_row = ttk.Frame(analytics_tab)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Refresh Metrics", command=self.refresh_analytics).pack(side="left")
        ttk.Button(
            btn_row,
            text="Export Tickets to CSV",
            style="Accent.TButton",
            command=self.export_csv,
        ).pack(side="right")

        self.tickets_cache = {}
        self.load_tickets()
        self.refresh_analytics()

    def load_tickets(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tickets_cache.clear()

        for t in get_all_tickets():
            self.tickets_cache[t["ticket_id"]] = t
            self.tree.insert(
                "",
                "end",
                iid=t["ticket_id"],
                values=(
                    t["ticket_id"],
                    t["hostname"],
                    t["error_code"],
                    t["itil_category"],
                    t["priority"],
                    t["support_mode"],
                    t["assigned_tier"],
                    t["status"],
                ),
            )

    def on_ticket_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        t = self.tickets_cache.get(selected[0])
        if not t:
            return

        pin_info = (
            f"AUTHORIZED (Session PIN: {t['remote_consent_pin']})"
            if t["remote_consent_pin"]
            else "NOT GRANTED (Respect Client Preference)"
        )
        details = (
            f"TICKET: {t['ticket_id']}  |  CLIENT: {t['client_username']} ({t['hostname']})  |  CREATED: {t['created_at']}\n"
            f"REMOTE ACCESS STATUS: {pin_info}\n"
            f"RAW DIAGNOSTIC: {t['technical_summary']}\n"
            f"{'-' * 82}\n"
            f"{t['ai_plain_explanation']}\n"
            f"EXISTING TECH NOTES: {t['tech_notes'] or 'None'}"
        )
        self.ai_box.config(state="normal")
        self.ai_box.delete("1.0", tk.END)
        self.ai_box.insert("1.0", details)
        self.ai_box.config(state="disabled")

    def handle_escalate(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a ticket to escalate.")
            return
        ticket_id = selected[0]
        escalate_ticket(ticket_id, self.notes_entry.get())
        self.notes_entry.delete(0, tk.END)
        self.load_tickets()
        self.refresh_analytics()
        messagebox.showinfo("Escalated", f"Ticket {ticket_id} transferred to Tier 2 Specialist Engineering.")

    def handle_resolve(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a ticket to resolve.")
            return
        ticket_id = selected[0]
        resolve_ticket(ticket_id, self.notes_entry.get())
        self.notes_entry.delete(0, tk.END)
        self.load_tickets()
        self.refresh_analytics()
        messagebox.showinfo("Resolved", f"Ticket {ticket_id} marked as Resolved.")

    def refresh_analytics(self):
        tickets = get_all_tickets()
        total = len(tickets)
        if total == 0:
            summary = "No ticket data available yet. Log a ticket from a Client account to generate insights."
        else:
            self_fixed = sum(1 for t in tickets if "Self-Service" in t["status"])
            escalated = sum(1 for t in tickets if t["status"] == "Escalated")
            resolved = sum(1 for t in tickets if "Resolved" in t["status"])
            open_count = sum(1 for t in tickets if t["status"] == "Open")

            cat_counts = {}
            code_counts = {}
            for t in tickets:
                cat_counts[t["itil_category"]] = cat_counts.get(t["itil_category"], 0) + 1
                code_counts[t["error_code"]] = code_counts.get(t["error_code"], 0) + 1

            self_rate = round((self_fixed / total) * 100, 1)
            res_rate = round((resolved / total) * 100, 1)

            lines = [
                "DESKBRIDGE OPERATIONAL ANALYTICS & TICKET INSIGHTS",
                "=" * 60,
                f"Total Tickets Logged        : {total}",
                f"Open / Active Queue         : {open_count}",
                f"Escalated to Tier 2         : {escalated}",
                f"Total Resolved (All Modes)  : {resolved} ({res_rate}%)",
                f"Tier-0 Self-Service Deflect : {self_fixed} ({self_rate}% saved from IT queue)",
                "",
                "TOP RECURRING ITIL CATEGORIES:",
            ]
            for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {cat:<28} : {count} ticket(s)")

            lines.append("\nTOP SPECIALIZED ERROR CODES:")
            for code, count in sorted(code_counts.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {code:<28} : {count} occurrence(s)")

            summary = "\n".join(lines)

        self.analytics_text.config(state="normal")
        self.analytics_text.delete("1.0", tk.END)
        self.analytics_text.insert("1.0", summary)
        self.analytics_text.config(state="disabled")

    def export_csv(self):
        tickets = get_all_tickets()
        if not tickets:
            messagebox.showwarning("No Data", "No tickets available to export.")
            return
        filename = f"deskbridge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=tickets[0].keys())
            writer.writeheader()
            writer.writerows(tickets)
        messagebox.showinfo("Export Complete", f"Analytics data exported to:\n{filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DeskBridgeApp(root)
    root.mainloop()
