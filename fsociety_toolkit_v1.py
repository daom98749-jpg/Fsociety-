#!/usr/bin/env python3
"""
fsociety-toolkit v3.0
Bo cong cu recon mang co ban - chay duoc tren Windows, Linux, Termux.
Chi gom cac chuc nang thu thap thong tin hop phap:
  - Thong tin IP cong khai
  - Port scanner (TCP connect scan don gian)
  - Banner grabbing tren cong mo
  - HTTP inspector (status, headers, security headers check)
  - DNS lookup (A/AAAA) + reverse DNS
  - Traceroute / ping toi muc tieu
  - WHOIS tra cuu domain (qua API cong khai)
  - Thong tin he thong
  - Xuat bao cao ra file JSON

Khong co chuc nang tan cong, khai thac lo hong, do mat khau, DDoS...
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json
import os
import platform
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

# ----------------------------------------------------------------------
# Mau sac: tu dong tat ANSI neu khong ho tro (vd cmd.exe cu), dung colorama
# neu co san tren Windows, khong bat buoc cai dat.
# ----------------------------------------------------------------------
IS_WINDOWS = platform.system().lower() == "windows"
COLOR_OK = True

if IS_WINDOWS:
    # Bat UTF-8 cho console de hien thi dung banner ky tu khoi (block chars)
    try:
        os.system("chcp 65001 >nul")
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        import colorama
        colorama.init(autoreset=False)
    except ImportError:
        # Thu bat ANSI native tren Windows 10+ (VirtualTerminalProcessing)
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            COLOR_OK = False

def _c(code):
    return code if COLOR_OK else ""

R = _c("\033[1;31m")
G = _c("\033[1;32m")
Y = _c("\033[1;33m")
B = _c("\033[1;34m")
C = _c("\033[1;36m")
W = _c("\033[1;37m")
RST = _c("\033[0m")

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
    3306, 3389, 5432, 6379, 8080, 8443, 27017
]

REPORT = {
    "generated_at": None,
    "entries": [],
}


def log_report(section, data):
    REPORT["entries"].append({
        "section": section,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "data": data,
    })


def clear():
    os.system("cls" if IS_WINDOWS else "clear")


def pause():
    input(f"\n{C}Nhan Enter de quay lai menu...{RST}")


def banner():
    clear()
    print(f"""{R}
  ███████╗███████╗ ██████╗  ██████╗██╗███████╗████████╗██╗   ██╗
  ██╔════╝██╔════╝██╔═══██╗██╔════╝██║██╔════╝╚══██╔══╝╚██╗ ██╔╝
  █████╗  ███████╗██║   ██║██║     ██║█████╗     ██║    ╚████╔╝
  ██╔══╝  ╚════██║██║   ██║██║     ██║██╔══╝     ██║     ╚██╔╝
  ██║     ███████║╚██████╔╝╚██████╗██║███████╗   ██║      ██║
  ╚═╝     ╚══════╝ ╚═════╝  ╚═════╝╚═╝╚══════╝   ╚═╝      ╚═╝
{RST}{C}      [ network recon toolkit v3.0 | {"Windows" if IS_WINDOWS else "Unix/Termux"} ]{RST}
""")


def fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "fsociety-toolkit/3.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


# ----------------------------------------------------------------------
# 1. Thong tin IP cong khai
# ----------------------------------------------------------------------
def public_ip_info():
    print(f"\n{G}[+] Dang truy van thong tin IP cong khai...{RST}")
    try:
        data = fetch_json("https://ipinfo.io/json")
        for key in ("ip", "hostname", "city", "region", "country", "org", "timezone"):
            if key in data:
                print(f"  {Y}{key:<10}:{RST} {W}{data[key]}{RST}")
        log_report("public_ip_info", data)
    except Exception as exc:
        print(f"{R}[!] Khong lay duoc thong tin IP: {exc}{RST}")


# ----------------------------------------------------------------------
# 2. Port scanner + banner grabbing
# ----------------------------------------------------------------------
def grab_banner(host, port, timeout=1.5):
    """Thu doc banner tra ve tu dich vu dang chay tren cong mo (thu dong, khong gui payload tan cong)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            # HTTPS/TLS can handshake rieng
            if port in (443, 8443):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert(binary_form=False)
                    return "TLS/SSL service"
            sock.settimeout(timeout)
            data = sock.recv(256)
            text = data.decode("utf-8", errors="replace").strip()
            return text[:120] if text else ""
    except Exception:
        return ""


def scan_single_port(host, port, timeout=1.0):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        if sock.connect_ex((host, port)) == 0:
            try:
                service = socket.getservbyport(port, "tcp")
            except OSError:
                service = "unknown"
            return port, service
    return None


def port_scanner():
    target = input(f"\n{W}Nhap domain hoac IP muc tieu: {RST}").strip()
    if not target:
        print(f"{R}[!] Chua nhap muc tieu.{RST}")
        return

    try:
        resolved_ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(f"{R}[!] Khong phan giai duoc ten mien/IP: {target}{RST}")
        return

    print(f"{C}[*] Muc tieu: {target} ({resolved_ip}){RST}")
    print(f"{Y}1.{RST} Quet nhanh cong pho bien ({len(COMMON_PORTS)} cong)")
    print(f"{Y}2.{RST} Quet dai cong tuy chinh (vi du: 1-1024)")
    mode = input(f"{W}Chon che do [1/2]: {RST}").strip()

    if mode == "2":
        rng = input(f"{W}Nhap dai cong (start-end): {RST}").strip()
        try:
            start_s, end_s = rng.split("-", 1)
            start_p, end_p = int(start_s), int(end_s)
            if not (1 <= start_p <= end_p <= 65535):
                raise ValueError
            if end_p - start_p > 5000:
                print(f"{Y}[!] Dai cong lon, gioi han quet 5000 cong dau de tranh qua tai.{RST}")
                end_p = start_p + 4999
            ports = list(range(start_p, end_p + 1))
        except ValueError:
            print(f"{R}[!] Dai cong khong hop le.{RST}")
            return
    else:
        ports = COMMON_PORTS

    do_banner = input(f"{W}Thu banner grabbing tren cong mo? (y/N): {RST}").strip().lower() == "y"

    print(f"\n{G}[+] Dang quet {len(ports)} cong TCP...{RST}")
    start_time = time.time()
    open_ports = []

    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(scan_single_port, resolved_ip, p) for p in ports]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                open_ports.append(res)

    open_ports.sort(key=lambda x: x[0])
    elapsed = time.time() - start_time

    results = []
    if open_ports:
        print(f"\n{G}[OK] Cac cong dang mo ({elapsed:.2f}s):{RST}")
        for port, svc in open_ports:
            banner_text = ""
            if do_banner:
                banner_text = grab_banner(resolved_ip, port)
            line = f"  {C}Port {port:<5}{RST} -> {G}OPEN{RST} ({svc})"
            if banner_text:
                line += f"  {Y}| banner:{RST} {banner_text}"
            print(line)
            results.append({"port": port, "service": svc, "banner": banner_text})
    else:
        print(f"\n{Y}[-] Khong phat hien cong mo nao trong danh sach quet ({elapsed:.2f}s).{RST}")

    log_report("port_scan", {
        "target": target,
        "resolved_ip": resolved_ip,
        "ports_scanned": len(ports),
        "open_ports": results,
        "elapsed_seconds": round(elapsed, 2),
    })


# ----------------------------------------------------------------------
# 3. HTTP inspector + security headers check
# ----------------------------------------------------------------------
SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


def http_inspector():
    url = input(f"\n{W}Nhap URL (vd: https://example.com): {RST}").strip()
    if not url:
        return
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n{G}[+] Dang kiem tra {url}...{RST}")
    headers_dict = {}
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0 (fsociety-toolkit)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  {Y}Status     :{RST} {G}{resp.status} {resp.reason}{RST}")
            print(f"  {Y}Final URL  :{RST} {resp.geturl()}")
            for k, v in resp.getheaders():
                headers_dict[k] = v
                print(f"  {C}{k:<28}:{RST} {v}")
    except urllib.error.HTTPError as err:
        print(f"  {Y}HTTP Error :{RST} {R}{err.code} {err.reason}{RST}")
        for k, v in err.headers.items():
            headers_dict[k] = v
            print(f"  {C}{k:<28}:{RST} {v}")
    except Exception as exc:
        print(f"{R}[!] Loi ket noi: {exc}{RST}")
        return

    print(f"\n{G}[+] Kiem tra security headers:{RST}")
    missing = []
    for h in SECURITY_HEADERS:
        if h in headers_dict:
            print(f"  {G}[v]{RST} {h}")
        else:
            print(f"  {R}[x]{RST} {h} {Y}(thieu){RST}")
            missing.append(h)

    log_report("http_inspector", {
        "url": url,
        "headers": headers_dict,
        "missing_security_headers": missing,
    })


# ----------------------------------------------------------------------
# 4. DNS lookup + reverse DNS
# ----------------------------------------------------------------------
def dns_lookup():
    host = input(f"\n{W}Nhap domain can tra cuu DNS: {RST}").strip()
    if not host:
        return
    print(f"\n{G}[+] Ban ghi dia chi cho {host}:{RST}")
    records = []
    try:
        infos = socket.getaddrinfo(host, None)
        seen = set()
        for info in infos:
            ip = info[4][0]
            family = "IPv6" if info[0] == socket.AF_INET6 else "IPv4"
            if (family, ip) not in seen:
                seen.add((family, ip))
                print(f"  {Y}{family:<6}:{RST} {W}{ip}{RST}")
                records.append({"type": family, "ip": ip})
    except socket.gaierror as exc:
        print(f"{R}[!] Khong tim thay ban ghi DNS: {exc}{RST}")
        return

    if input(f"\n{W}Tra reverse DNS cho IP dau tien? (y/N): {RST}").strip().lower() == "y" and records:
        try:
            rev = socket.gethostbyaddr(records[0]["ip"])
            print(f"  {C}Reverse DNS:{RST} {rev[0]}")
            log_report("dns_lookup", {"host": host, "records": records, "reverse": rev[0]})
            return
        except Exception as exc:
            print(f"{R}[!] Khong tra duoc reverse DNS: {exc}{RST}")

    log_report("dns_lookup", {"host": host, "records": records})


# ----------------------------------------------------------------------
# 5. Ping / Traceroute (dung lenh he thong co san, khong tu viet raw socket)
# ----------------------------------------------------------------------
def ping_host():
    target = input(f"\n{W}Nhap host de ping: {RST}").strip()
    if not target:
        return
    count_flag = "-n" if IS_WINDOWS else "-c"
    cmd = ["ping", count_flag, "4", target]
    print(f"\n{G}[+] Dang ping {target}...{RST}\n")
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print(f"{R}[!] Khong tim thay lenh ping tren he thong.{RST}")


def traceroute_host():
    target = input(f"\n{W}Nhap host de traceroute: {RST}").strip()
    if not target:
        return
    cmd = ["tracert", target] if IS_WINDOWS else ["traceroute", target]
    print(f"\n{G}[+] Dang traceroute toi {target} (co the mat vai giay)...{RST}\n")
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        alt = "tracert" if not IS_WINDOWS else "traceroute"
        print(f"{R}[!] Khong tim thay lenh traceroute/tracert. (thu cai {alt} neu can){RST}")


# ----------------------------------------------------------------------
# 6. WHOIS tra cuu domain qua API cong khai (khong can cai them thu vien)
# ----------------------------------------------------------------------
def whois_lookup():
    domain = input(f"\n{W}Nhap domain can tra WHOIS: {RST}").strip()
    if not domain:
        return
    print(f"\n{G}[+] Dang tra cuu WHOIS cho {domain}...{RST}")
    try:
        data = fetch_json(f"https://rdap.org/domain/{domain}")
        print(f"  {Y}Domain      :{RST} {data.get('ldhName', domain)}")
        events = data.get("events", [])
        for ev in events:
            action = ev.get("eventAction", "")
            date = ev.get("eventDate", "")
            print(f"  {Y}{action:<12}:{RST} {date}")
        nameservers = [ns.get("ldhName", "") for ns in data.get("nameservers", [])]
        if nameservers:
            print(f"  {Y}Nameservers :{RST} {', '.join(nameservers)}")
        statuses = data.get("status", [])
        if statuses:
            print(f"  {Y}Status      :{RST} {', '.join(statuses)}")
        log_report("whois", {"domain": domain, "raw": data})
    except Exception as exc:
        print(f"{R}[!] Khong tra duoc WHOIS (domain co the khong ho tro RDAP): {exc}{RST}")


# ----------------------------------------------------------------------
# 7. Thong tin he thong
# ----------------------------------------------------------------------
def sys_info():
    print(f"\n{G}[+] Thong tin he thong:{RST}")
    print(f"  {Y}OS / Kernel :{RST} {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"  {Y}Python      :{RST} {platform.python_version()}")
    print(f"  {Y}Hostname    :{RST} {socket.gethostname()}")

    if IS_WINDOWS:
        drive = os.environ.get("SystemDrive", "C:") + "\\"
        if os.path.exists(drive):
            total, used, free = shutil.disk_usage(drive)
            gib = 1024 ** 3
            print(f"  {Y}O {drive:<9}:{RST} {used / gib:.2f} GiB / {total / gib:.2f} GiB (Trong {free / gib:.2f} GiB)")
    else:
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        path_to_check = prefix if os.path.exists(prefix) else "/"
        total, used, free = shutil.disk_usage(path_to_check)
        gib = 1024 ** 3
        print(f"  {Y}Disk        :{RST} {used / gib:.2f} GiB / {total / gib:.2f} GiB (Trong {free / gib:.2f} GiB)")


# ----------------------------------------------------------------------
# 8. Xuat bao cao
# ----------------------------------------------------------------------
def export_report():
    if not REPORT["entries"]:
        print(f"{Y}[!] Chua co du lieu nao de xuat. Hay chay vai chuc nang truoc.{RST}")
        return
    REPORT["generated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    default_name = f"fsociety_report_{int(time.time())}.json"
    name = input(f"\n{W}Ten file xuat (Enter de dung '{default_name}'): {RST}").strip() or default_name
    try:
        with open(name, "w", encoding="utf-8") as fh:
            json.dump(REPORT, fh, indent=2, ensure_ascii=False)
        full_path = os.path.abspath(name)
        print(f"{G}[OK] Da luu bao cao tai: {full_path}{RST}")
    except Exception as exc:
        print(f"{R}[!] Khong the ghi file: {exc}{RST}")


# ----------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------
MENU_ACTIONS = {
    "1": ("Xem IP cong khai & thong tin mang", public_ip_info),
    "2": ("Quet cong TCP + banner grabbing", port_scanner),
    "3": ("Kiem tra HTTP status/headers + security headers", http_inspector),
    "4": ("Tra cuu DNS (A/AAAA) + reverse DNS", dns_lookup),
    "5": ("Ping host", ping_host),
    "6": ("Traceroute toi host", traceroute_host),
    "7": ("Tra cuu WHOIS domain", whois_lookup),
    "8": ("Thong tin thiet bi", sys_info),
    "9": ("Xuat bao cao JSON tu cac ket qua da chay", export_report),
}


def main():
    while True:
        banner()
        for key, (label, _) in MENU_ACTIONS.items():
            print(f"  {Y}[{key}]{RST} {label}")
        print(f"  {R}[0]{RST} Thoat\n")

        choice = input(f"{C}fsociety{RST}:{W}~{RST}$ ").strip()
        if choice == "0":
            print(f"\n{R}Good luck.{RST}")
            sys.exit(0)
        action = MENU_ACTIONS.get(choice)
        if action:
            _, func = action
            try:
                func()
            except KeyboardInterrupt:
                print(f"\n{Y}[!] Da huy thao tac.{RST}")
            pause()
        else:
            print(f"{R}[!] Lua chon khong hop le.{RST}")
            time.sleep(0.8)


if __name__ == "__main__":
    main()
