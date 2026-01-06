"""
Neo4j Knowledge Graph Initialization Script
Populates Neo4j with nmap options and conflict relationships

Run: python scripts/init_neo4j.py
"""

import os
from neo4j import GraphDatabase


def init_knowledge_graph():
    """Initialize Neo4j with nmap options and conflicts"""
    
    # Connect to Neo4j
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password123")
    
    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Clear existing data
        print("Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create Options
        print("Creating nmap options...")
        
        options = [
            # Scan Types
            {"name": "-sS", "category": "SCAN_TYPE", "description": "TCP SYN scan (stealth)", "requires_root": True, "requires_args": False},
            {"name": "-sT", "category": "SCAN_TYPE", "description": "TCP connect scan", "requires_root": False, "requires_args": False},
            {"name": "-sU", "category": "SCAN_TYPE", "description": "UDP scan", "requires_root": True, "requires_args": False},
            {"name": "-sN", "category": "SCAN_TYPE", "description": "TCP NULL scan", "requires_root": True, "requires_args": False},
            {"name": "-sF", "category": "SCAN_TYPE", "description": "FIN scan", "requires_root": True, "requires_args": False},
            {"name": "-sX", "category": "SCAN_TYPE", "description": "Xmas scan", "requires_root": True, "requires_args": False},
            {"name": "-sA", "category": "SCAN_TYPE", "description": "ACK scan", "requires_root": True, "requires_args": False},
            {"name": "-sW", "category": "SCAN_TYPE", "description": "Window scan", "requires_root": True, "requires_args": False},
            {"name": "-sM", "category": "SCAN_TYPE", "description": "Maimon scan", "requires_root": True, "requires_args": False},
            
            # Discovery
            {"name": "-sn", "category": "DISCOVERY", "description": "Ping scan (no port scan)", "requires_root": False, "requires_args": False},
            
            # Port Specification
            {"name": "-p", "category": "PORT_SPEC", "description": "Port specification", "requires_root": False, "requires_args": True},
            {"name": "-p-", "category": "PORT_SPEC", "description": "All 65535 ports", "requires_root": False, "requires_args": False},
            {"name": "-F", "category": "PORT_SPEC", "description": "Fast scan (100 ports)", "requires_root": False, "requires_args": False},
            {"name": "--top-ports", "category": "PORT_SPEC", "description": "Scan top N ports", "requires_root": False, "requires_args": True},
            
            # Service Detection
            {"name": "-sV", "category": "SERVICE_DETECTION", "description": "Version detection", "requires_root": False, "requires_args": False},
            
            # OS Detection
            {"name": "-O", "category": "OS_DETECTION", "description": "OS detection", "requires_root": True, "requires_args": False},
            
            # Timing
            {"name": "-T0", "category": "TIMING", "description": "Paranoid timing", "requires_root": False, "requires_args": False},
            {"name": "-T1", "category": "TIMING", "description": "Sneaky timing", "requires_root": False, "requires_args": False},
            {"name": "-T2", "category": "TIMING", "description": "Polite timing", "requires_root": False, "requires_args": False},
            {"name": "-T3", "category": "TIMING", "description": "Normal timing", "requires_root": False, "requires_args": False},
            {"name": "-T4", "category": "TIMING", "description": "Aggressive timing", "requires_root": False, "requires_args": False},
            {"name": "-T5", "category": "TIMING", "description": "Insane timing", "requires_root": False, "requires_args": False},
            
            # Scripts
            {"name": "--script", "category": "SCRIPTING", "description": "NSE scripts", "requires_root": False, "requires_args": True},
            
            # Output
            {"name": "-oX", "category": "OUTPUT", "description": "XML output", "requires_root": False, "requires_args": True},
            {"name": "-oN", "category": "OUTPUT", "description": "Normal output", "requires_root": False, "requires_args": True},
            {"name": "-oG", "category": "OUTPUT", "description": "Grepable output", "requires_root": False, "requires_args": True},
            
            # Misc
            {"name": "--traceroute", "category": "MISC", "description": "Trace route to host", "requires_root": False, "requires_args": False},
            {"name": "-6", "category": "MISC", "description": "IPv6 scanning", "requires_root": False, "requires_args": False},
            {"name": "-A", "category": "AGGRESSIVE", "description": "Aggressive scan", "requires_root": True, "requires_args": False},
            {"name": "-v", "category": "OUTPUT", "description": "Verbose", "requires_root": False, "requires_args": False},
            {"name": "-Pn", "category": "HOST_DISCOVERY", "description": "Skip host discovery", "requires_root": False, "requires_args": False},
        ]
        
        for opt in options:
            session.run(
                """
                CREATE (o:Option {
                    name: $name,
                    category: $category,
                    description: $description,
                    requires_root: $requires_root,
                    requires_args: $requires_args
                })
                """,
                **opt
            )
        
        print(f"✅ Created {len(options)} options")
        
        # Create Conflicts
        print("Creating conflict relationships...")
        
        conflicts = [
            # Scan type conflicts (mutual)
            ("-sS", "-sT"), ("-sS", "-sU"), ("-sS", "-sN"), ("-sS", "-sF"), ("-sS", "-sX"), ("-sS", "-sA"), ("-sS", "-sW"), ("-sS", "-sM"),
            ("-sT", "-sU"), ("-sT", "-sN"), ("-sT", "-sF"), ("-sT", "-sX"), ("-sT", "-sA"), ("-sT", "-sW"), ("-sT", "-sM"),
            ("-sU", "-sN"), ("-sU", "-sF"), ("-sU", "-sX"), ("-sU", "-sA"), ("-sU", "-sW"), ("-sU", "-sM"),
            ("-sN", "-sF"), ("-sN", "-sX"), ("-sN", "-sA"), ("-sN", "-sW"), ("-sN", "-sM"),
            ("-sF", "-sX"), ("-sF", "-sA"), ("-sF", "-sW"), ("-sF", "-sM"),
            ("-sX", "-sA"), ("-sX", "-sW"), ("-sX", "-sM"),
            ("-sA", "-sW"), ("-sA", "-sM"),
            ("-sW", "-sM"),
            
            # Special conflicts
            ("-sn", "-p"),
            ("-sn", "-sS"), ("-sn", "-sT"), ("-sn", "-sU"),
            
            # Timing conflicts
            ("-T0", "-T1"), ("-T0", "-T2"), ("-T0", "-T3"), ("-T0", "-T4"), ("-T0", "-T5"),
            ("-T1", "-T2"), ("-T1", "-T3"), ("-T1", "-T4"), ("-T1", "-T5"),
            ("-T2", "-T3"), ("-T2", "-T4"), ("-T2", "-T5"),
            ("-T3", "-T4"), ("-T3", "-T5"),
            ("-T4", "-T5"),
            
            # Port spec conflicts
            ("-p-", "-F"), ("-p-", "--top-ports"),
            ("-p", "-F"),
        ]
        
        conflict_count = 0
        for opt1, opt2 in conflicts:
            # Create bidirectional conflict
            session.run(
                """
                MATCH (o1:Option {name: $opt1}), (o2:Option {name: $opt2})
                CREATE (o1)-[:CONFLICTS_WITH]->(o2)
                CREATE (o2)-[:CONFLICTS_WITH]->(o1)
                """,
                opt1=opt1, opt2=opt2
            )
            conflict_count += 2
        
        print(f"✅ Created {conflict_count} conflict relationships")
        
        # Verify
        result = session.run("MATCH (o:Option) RETURN count(o) as count")
        option_count = result.single()["count"]
        
        result = session.run("MATCH ()-[r:CONFLICTS_WITH]->() RETURN count(r) as count")
        conflict_rel_count = result.single()["count"]
        
        print("\n" + "="*70)
        print("✅ Neo4j Knowledge Graph Initialized!")
        print("="*70)
        print(f"Options: {option_count}")
        print(f"Conflicts: {conflict_rel_count}")
        print("\nTest queries:")
        print("  MATCH (o:Option) RETURN o LIMIT 10;")
        print("  MATCH (o1)-[:CONFLICTS_WITH]->(o2) RETURN o1.name, o2.name LIMIT 10;")
        print("="*70)
    
    driver.close()


if __name__ == "__main__":
    init_knowledge_graph()