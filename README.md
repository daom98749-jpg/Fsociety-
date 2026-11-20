# Fsociety Toolkit

A basic network recon toolkit that runs on Windows, Linux, and Termux (Android).

Includes only legitimate information-gathering functions — no attack, exploitation, or password-cracking capabilities.

## Features

- Public IP lookup
- Port scanner (TCP connect scan) + banner grabbing
- HTTP status / headers check + security headers audit
- DNS lookup (A/AAAA) + reverse DNS
- Ping / Traceroute
- Domain WHOIS lookup
- System info
- Export scan results to a JSON report

## Requirements

- Python 3.8+
- No external dependencies required (standard library only)

## Usage

### Windows

```bash
py fsociety_toolkit_v1.py
```

### Linux / Termux

```bash
python3 fsociety_toolkit_v1.py
```

## Example

After running, a menu will appear:

```
  [1] Public IP & network info
  [2] TCP port scan + banner grabbing
  [3] HTTP status/headers + security headers check
  [4] DNS lookup (A/AAAA) + reverse DNS
  [5] Ping host
  [6] Traceroute to host
  [7] Domain WHOIS lookup
  [8] System info
  [9] Export JSON report from results so far
  [0] Exit
```

Enter a number and press Enter to use that feature.

### Example: scanning common ports on a domain

```
fsociety:~$ 2
Enter target domain or IP: example.com
1. Quick scan of common ports (17 ports)
2. Custom port range (e.g. 1-1024)
Choose mode [1/2]: 1
```

### Example: checking a website's security headers

```
fsociety:~$ 3
Enter URL (e.g. https://example.com): https://example.com
```

The output shows which security headers (HSTS, CSP, X-Frame-Options, etc.) are present or missing.

## License

This project is for educational and legitimate network-testing purposes only, on systems you own or are authorized to test.
