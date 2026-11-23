#### DeskBridge-HelpDesk

**Status:** 🚧 Active Development (MVP Phase)
**Author:** Thato Dintso 

A lightweight, Python-based help desk and system diagnostics application designed to bridge the gap between end-users (Clients) and IT Support Teams (Internal IT or Outsourced MSPs). 

Instead of forcing non-technical users to explain complex system errors, this tool captures real-time machine diagnostics via a single hotkey, guides users through self-troubleshooting when possible, and generates structured, ITIL-aligned tickets with actionable analytics for technicians. 

#### 🎯 The Problem It Solves

1. **Vague Tickets ("Blank Ticket" Syndrome):** End-users often submit unclear requests (*"My Wi-Fi isn't working"*), wasting valuable Tier 1 support time.
2. **Unnecessary Escalations:** Simple issues (like stale DNS caches or minor network drops) clog up help desk queues when users could fix them safely with guided steps.
3. **Lack of User Consent & Flexibility:** Users often feel uncomfortable granting immediate remote desktop access without clear consent or alternative options (voice/video walkthroughs or walk-in support).

#### ✨ Core Features

#### 👤 Client Account (End-User Side)

* **Instant Hotkey Trigger (Ctrl + .):** Runs quietly in the background and launches a diagnostic scan on demand.
* **Automated System Triage:** Checks network connectivity, DNS resolution, disk health, and critical system logs.
* **Tier 0 Self-Service:** Displays clear, step-by-step troubleshooting instructions for common issues the user can resolve immediately.
* **Smart Ticket Logging:** Automatically maps unresolved faults to structured **ITIL categories**, assigns priority levels (P1–P4), generates a diagnostic error code, and issues a unique Ticket ID.
* **Flexible Support Preferences:** Lets the client choose how they want help: 

  * Self-Troubleshoot (with guided steps)
  * Consent-Based Remote Access (generates a temporary session authorization token)
  * Voice / Video Guided Walkthrough
  * Walk-In IT Support Booking

#### 🛠️ IT Team Account (Technician & MSP Side)

* **Role-Based Access Control:** Separate workspace for internal IT staff or outsourced support providers.
* **Error Code & Log Translator:** Converts specialized diagnostic codes and raw system telemetry into plain-English fault summaries (with optional AI-assisted root-cause analysis).
* **Tiered Escalation Workflow:** One-click escalation from Tier 1 to Tier 2/Tier 3 support with full diagnostic context preserved.
* **Data & Analytics Dashboard:** Transforms raw ticket logs into actionable insights—tracking recurring error categories, self-service resolution rates, and average resolution times.


🚀 How to Run (Zero External Dependencies)

DeskBridge is built using Python 3.12+ standard libraries (tkinter, sqlite3, subprocess, socket, ctypes, csv) so anyone can clone and run it immediately without installing heavy packages:
bash
git clone https://github.com/BLAQX007/DeskBridge-HELPDESK.git
cd DeskBridge-HELPDESK
python main.py
Use code with caution.

🔑 Demo Login Accounts


Role	Username	Password
Client (End-User)
	client1	pass123
Internal IT Support (Tier 1)
	tech1	admin123
Outsourced MSP Technician
	msp_tech	msp123


🗺️ Development Roadmap

• [x] Phase 1: Core Windows diagnostic scanner & ITIL error-code mapper (diagnostics.py)
• [x] Phase 2: Dual-account authentication (Client vs. IT Team) & SQLite ticket database (database.py)
• [x] Phase 3: Hotkey listener (Ctrl + .), consent-based support workflow, and Tier 1 → Tier 2 escalation (main.py)
• [x] Phase 4: Ticket analytics & CSV reporting dashboard (main.py)
• [ ] Phase 5 (Planned): Live LLM API toggle & encrypted socket screen-sharing tunnel
#### 🔒 Copyright & Usage

© 2026 Thato Dintso. All Rights Reserved.
This repository is shared publicly for portfolio and technical demonstration purposes. Unauthorized copying, redistribution, or commercial use of this code without explicit permission is prohibited.
