import time
from agents.validator.validator import CommandValidator

validator = CommandValidator()
commands = [
    "nmap -sV 192.168.1.1",
    "nmap -sS -p 80,443 192.168.1.1",
    # ... 100 commandes
]

start = time.time()
for cmd in commands:
    validator.full_validation(cmd)
end = time.time()

print(f"Validated {len(commands)} commands in {end-start:.2f}s")
print(f"Average: {(end-start)/len(commands)*1000:.2f}ms per command")
