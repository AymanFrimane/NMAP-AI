#!/usr/bin/env python3
"""Quick KG Test - One command to verify everything works"""

from agents.comprehension.kg_utils import get_options, get_conflicts, get_port_info

print("Testing KG...")
print(f"✅ Options loaded: {len(get_options())}")
print(f"✅ Scan types: {[o.name for o in get_options(category='SCAN_TYPE')]}")
print(f"✅ Conflicts for -sS: {get_conflicts('-sS')}")
print(f"✅ SSH port: {get_port_info(service='SSH').number}")
print("🎉 KG is working!")