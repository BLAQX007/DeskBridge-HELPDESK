import subprocess
import socket
import shutil
import platform
import ctypes
from datetime import datetime


def check_internet_connectivity(host="8.8.8.8", timeout=2):
    """Pings Google DNS to verify raw internet connectivity."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", "-w", str(timeout * 1000), host]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def check_dns_resolution(domain="://google.com"):
    """Checks if domain names resolve properly to IP addresses."""
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def check_disk_space(path="C:\\"):
    """Checks free disk space percentage on the primary drive."""
    total, used, free = shutil.disk_usage(path)
    free_percent = round((free / total) * 100, 1)
    free_gb = round(free / (1024**3), 1)
    return free_percent, free_gb


def check_ram_usage():
    """Uses Windows built-in API to check physical RAM usage without extra libraries."""
    if platform.system().lower() != "windows":
        return 0.0

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return float(stat.dwMemoryLoad)


def run_system_diagnostics():
    """
    Runs a full diagnostic triage and returns a structured ITIL report.
    Determines if the client can self-fix (Tier 0) or if IT escalation is required.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()}"

    internet_ok = check_internet_connectivity()
    dns_ok = check_dns_resolution() if internet_ok else False
    free_disk_pct, free_disk_gb = check_disk_space()
    ram_load_pct = check_ram_usage()

    # Triage Logic: Prioritizes the most critical fault first
    if not internet_ok:
        diagnosis = {
            "error_code": "NET-CONN-101",
            "itil_category": "Network & Connectivity",
            "priority": "P1 - Critical",
            "summary": "No outbound internet connection detected (Ping to 8.8.8.8 failed).",
            "can_self_fix": True,
            "self_fix_steps": [
                "1. Check if Wi-Fi is turned on or if your Ethernet cable is plugged in securely.",
                "2. Turn Airplane Mode ON for 10 seconds, then turn it OFF.",
                "3. Restart your Wi-Fi router or mobile hotspot.",
                "4. If the issue persists after 2 minutes, submit this ticket to IT Support."
            ]
        }
    elif not dns_ok:
        diagnosis = {
            "error_code": "NET-DNS-204",
            "itil_category": "Network & Connectivity",
            "priority": "P2 - High",
            "summary": "Internet is reachable, but DNS name resolution failed.",
            "can_self_fix": True,
            "self_fix_steps": [
                "1. Open Command Prompt and type: ipconfig /flushdns",
                "2. Disconnect and reconnect to your Wi-Fi network.",
                "3. Close and reopen your web browser.",
                "4. If websites still fail to load, escalate to IT Support."
            ]
        }
    elif free_disk_pct < 10.0:
        diagnosis = {
            "error_code": "HW-DISK-305",
            "itil_category": "Hardware & Storage",
            "priority": "P2 - High",
            "summary": f"Critically low disk space ({free_disk_pct}% / {free_disk_gb} GB remaining).",
            "can_self_fix": False,
            "self_fix_steps": [
                "Storage is critically full. IT Support intervention is recommended to safely clean system files or expand storage."
            ]
        }
    elif ram_load_pct > 90.0:
        diagnosis = {
            "error_code": "PERF-RAM-402",
            "itil_category": "System Performance",
            "priority": "P3 - Medium",
            "summary": f"High memory utilization detected ({ram_load_pct}% RAM in use).",
            "can_self_fix": True,
            "self_fix_steps": [
                "1. Close unused browser tabs and background applications.",
                "2. Press Ctrl + Shift + Esc to open Task Manager and check top memory apps.",
                "3. Save your work and restart your computer if performance remains slow."
            ]
        }
    else:
        diagnosis = {
            "error_code": "SYS-OK-000",
            "itil_category": "General Inquiry / Software",
            "priority": "P4 - Low",
            "summary": "Core network, DNS, disk, and memory checks passed. Issue may be application-specific.",
            "can_self_fix": False,
            "self_fix_steps": [
                "Automated hardware/network checks look healthy. Please select your preferred IT support option below."
            ]
        }

    return {
        "timestamp": timestamp,
        "hostname": hostname,
        "os_info": os_info,
        "telemetry": {
            "internet_connected": internet_ok,
            "dns_working": dns_ok,
            "disk_free_percent": free_disk_pct,
            "disk_free_gb": free_disk_gb,
            "ram_usage_percent": ram_load_pct,
        },
        "diagnosis": diagnosis
    }


# Quick standalone test when running diagnostics.py directly
if __name__ == "__main__":
    print("Running DeskBridge System Diagnostics...\n")
    report = run_system_diagnostics()
    print(f"Machine: {report['hostname']} ({report['os_info']})")
    print(f"Telemetry: {report['telemetry']}")
    print("-" * 50)
    diag = report["diagnosis"]
    print(f"Error Code   : {diag['error_code']}")
    print(f"ITIL Category: {diag['itil_category']}")
    print(f"Priority     : {diag['priority']}")
    print(f"Summary      : {diag['summary']}")
    print(f"Self-Fixable?: {'Yes' if diag['can_self_fix'] else 'No (Requires IT)'}")
    print("\nRecommended Steps:")
    for step in diag["self_fix_steps"]:
        print(f"  {step}")
