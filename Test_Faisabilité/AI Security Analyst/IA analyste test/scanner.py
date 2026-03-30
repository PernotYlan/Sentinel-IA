import nmap

def scan_ports(target):

    scanner = nmap.PortScanner()

    scanner.scan(target, '1-1024')

    result = ""

    for host in scanner.all_hosts():

        result += f"Host : {host}\n"
        result += f"State : {scanner[host].state()}\n"

        for proto in scanner[host].all_protocols():

            ports = scanner[host][proto].keys()

            for port in ports:

                state = scanner[host][proto][port]['state']

                result += f"Port {port} : {state}\n"

    return result