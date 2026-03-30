from ai_agent import ask_ai
from scanner import scan_ports
from reporter import generate_report

target = input("Cible à analyser (IP ou domaine): ")

print("\n[+] Scan des ports en cours...\n")

scan_result = scan_ports(target)

print(scan_result)

print("\n[+] Analyse IA...\n")

analysis = ask_ai(scan_result)

report = generate_report(target, scan_result, analysis)

print(report)

with open("rapport.txt", "w") as f:
    f.write(report)

print("\nRapport sauvegardé dans rapport.txt")