"""
Knowledge Graph Initialization Script
=====================================

This script initializes the Neo4j Knowledge Graph with comprehensive nmap option data.

PERSON 1 (P1) - Knowledge Graph Component
This is the official initialization script for the P1 component.

Usage:
    python agents/comprehension/init_kg.py

Requirements:
    - Neo4j running on bolt://localhost:7687
    - Neo4j credentials: neo4j/password123
    - neo4j-driver package installed

Author: Person 1 (Knowledge Graph)
Integration: Person 4 (Validator)
"""

import os
import sys
from typing import List, Tuple
from neo4j import GraphDatabase


class KnowledgeGraphInitializer:
    """Initialize Neo4j Knowledge Graph with nmap options and relationships."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize the KG initializer.
        
        Args:
            uri: Neo4j URI (default: from env or bolt://localhost:7687)
            user: Neo4j username (default: from env or neo4j)
            password: Neo4j password (default: from env or password123)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            print(f"✅ Connected to Neo4j at {self.uri}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print(f"   URI: {self.uri}")
            print(f"   User: {self.user}")
            print("\n💡 Tips:")
            print("   - Ensure Neo4j is running: docker-compose up -d")
            print("   - Check credentials match docker-compose.yml")
            print("   - Verify port 7687 is accessible")
            return False
    
    def clear_database(self):
        """Clear all existing data from the database."""
        print("\n🗑️  Clearing existing data...")
        
        with self.driver.session() as session:
            # Delete all relationships
            session.run("MATCH ()-[r]->() DELETE r")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            
            # Verify empty
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            
            print(f"   Database cleared (was {count} nodes)")
    
    def create_constraints(self):
        """Create uniqueness constraints for better performance."""
        print("\n🔧 Creating constraints...")
        
        with self.driver.session() as session:
            try:
                # Unique constraint on option names
                session.run("""
                    CREATE CONSTRAINT option_name_unique IF NOT EXISTS
                    FOR (o:Option) REQUIRE o.name IS UNIQUE
                """)
                print("   ✓ Created uniqueness constraint on Option.name")
            except Exception as e:
                print(f"   ⚠ Constraint already exists or error: {e}")
    
    def get_nmap_options(self) -> List[Tuple[dict, List[str]]]:
        """
        Get comprehensive nmap options data.
        
        Returns:
            List of tuples: (option_properties, list_of_conflicts)
        """
        options = [
            # ========== SCAN TYPES ==========
            ({
                "name": "-sS",
                "category": "SCAN_TYPE",
                "description": "TCP SYN scan (stealth scan) - half-open scanning",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sS 192.168.1.1",
                "complexity": "EASY"
            }, ["-sT", "-sU", "-sN", "-sF", "-sX", "-sn", "-sA", "-sW", "-sM"]),
            
            ({
                "name": "-sT",
                "category": "SCAN_TYPE",
                "description": "TCP connect scan - full TCP handshake",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -sT 192.168.1.1",
                "complexity": "EASY"
            }, ["-sS", "-sU", "-sN", "-sF", "-sX", "-sn", "-sA", "-sW", "-sM"]),
            
            ({
                "name": "-sU",
                "category": "SCAN_TYPE",
                "description": "UDP scan - scan UDP ports",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sU 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-sS", "-sT", "-sN", "-sF", "-sX", "-sn"]),
            
            ({
                "name": "-sN",
                "category": "SCAN_TYPE",
                "description": "TCP NULL scan - no flags set",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sN 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-sS", "-sT", "-sU", "-sF", "-sX", "-sn", "-sA"]),
            
            ({
                "name": "-sF",
                "category": "SCAN_TYPE",
                "description": "TCP FIN scan - FIN flag set",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sF 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-sS", "-sT", "-sU", "-sN", "-sX", "-sn", "-sA"]),
            
            ({
                "name": "-sX",
                "category": "SCAN_TYPE",
                "description": "TCP Xmas scan - FIN, PSH, and URG flags set",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sX 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-sS", "-sT", "-sU", "-sN", "-sF", "-sn", "-sA"]),
            
            ({
                "name": "-sA",
                "category": "SCAN_TYPE",
                "description": "TCP ACK scan - detect firewall rules",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sA 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-sS", "-sT", "-sN", "-sF", "-sX"]),
            
            ({
                "name": "-sW",
                "category": "SCAN_TYPE",
                "description": "TCP Window scan - detect open/closed ports via window size",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sW 192.168.1.1",
                "complexity": "HARD"
            }, ["-sS", "-sT"]),
            
            ({
                "name": "-sM",
                "category": "SCAN_TYPE",
                "description": "TCP Maimon scan - FIN/ACK probe",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -sM 192.168.1.1",
                "complexity": "HARD"
            }, ["-sS", "-sT"]),
            
            # ========== HOST DISCOVERY ==========
            ({
                "name": "-sn",
                "category": "HOST_DISCOVERY",
                "description": "Ping scan - disable port scan, only host discovery",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -sn 192.168.1.0/24",
                "complexity": "EASY"
            }, ["-sS", "-sT", "-sU", "-sN", "-sF", "-sX", "-p", "-F", "-p-", "--top-ports"]),
            
            ({
                "name": "-Pn",
                "category": "HOST_DISCOVERY",
                "description": "Skip host discovery - treat all hosts as online",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -Pn 192.168.1.1",
                "complexity": "EASY"
            }, ["-sn"]),
            
            ({
                "name": "-PS",
                "category": "HOST_DISCOVERY",
                "description": "TCP SYN ping - discover hosts via SYN packets",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -PS80,443 192.168.1.0/24",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "-PA",
                "category": "HOST_DISCOVERY",
                "description": "TCP ACK ping - discover hosts via ACK packets",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -PA80,443 192.168.1.0/24",
                "complexity": "MEDIUM"
            }, []),
            
            # ========== PORT SPECIFICATION ==========
            ({
                "name": "-p",
                "category": "PORT_SPEC",
                "description": "Specify ports to scan",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -p 80,443,8080 192.168.1.1",
                "complexity": "EASY"
            }, ["-F", "-p-", "--top-ports"]),
            
            ({
                "name": "-p-",
                "category": "PORT_SPEC",
                "description": "Scan all 65535 ports",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -p- 192.168.1.1",
                "complexity": "EASY"
            }, ["-p", "-F", "--top-ports"]),
            
            ({
                "name": "-F",
                "category": "PORT_SPEC",
                "description": "Fast scan - scan 100 most common ports",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -F 192.168.1.1",
                "complexity": "EASY"
            }, ["-p", "-p-", "--top-ports"]),
            
            ({
                "name": "--top-ports",
                "category": "PORT_SPEC",
                "description": "Scan N most common ports",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap --top-ports 10 192.168.1.1",
                "complexity": "EASY"
            }, ["-p", "-p-", "-F"]),
            
            # ========== SERVICE/VERSION DETECTION ==========
            ({
                "name": "-sV",
                "category": "SERVICE_DETECTION",
                "description": "Service version detection",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -sV 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "--version-intensity",
                "category": "SERVICE_DETECTION",
                "description": "Set version detection intensity (0-9)",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -sV --version-intensity 5 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            # ========== OS DETECTION ==========
            ({
                "name": "-O",
                "category": "OS_DETECTION",
                "description": "Enable OS detection",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -O 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "--osscan-limit",
                "category": "OS_DETECTION",
                "description": "Limit OS detection to promising targets",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -O --osscan-limit 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "--osscan-guess",
                "category": "OS_DETECTION",
                "description": "Guess OS more aggressively",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -O --osscan-guess 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            # ========== TIMING TEMPLATES ==========
            ({
                "name": "-T0",
                "category": "TIMING",
                "description": "Paranoid timing - extremely slow, IDS evasion",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T0 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-T1", "-T2", "-T3", "-T4", "-T5"]),
            
            ({
                "name": "-T1",
                "category": "TIMING",
                "description": "Sneaky timing - slow, IDS evasion",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T1 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-T0", "-T2", "-T3", "-T4", "-T5"]),
            
            ({
                "name": "-T2",
                "category": "TIMING",
                "description": "Polite timing - slows down to use less bandwidth",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T2 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-T0", "-T1", "-T3", "-T4", "-T5"]),
            
            ({
                "name": "-T3",
                "category": "TIMING",
                "description": "Normal timing - default timing",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T3 192.168.1.1",
                "complexity": "EASY"
            }, ["-T0", "-T1", "-T2", "-T4", "-T5"]),
            
            ({
                "name": "-T4",
                "category": "TIMING",
                "description": "Aggressive timing - faster, assumes fast network",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T4 192.168.1.1",
                "complexity": "EASY"
            }, ["-T0", "-T1", "-T2", "-T3", "-T5"]),
            
            ({
                "name": "-T5",
                "category": "TIMING",
                "description": "Insane timing - extremely fast, may miss results",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -T5 192.168.1.1",
                "complexity": "MEDIUM"
            }, ["-T0", "-T1", "-T2", "-T3", "-T4"]),
            
            # ========== SCRIPTING ENGINE ==========
            ({
                "name": "--script",
                "category": "SCRIPTING",
                "description": "Run NSE (Nmap Scripting Engine) scripts",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap --script vuln 192.168.1.1",
                "complexity": "HARD"
            }, []),
            
            ({
                "name": "--script-args",
                "category": "SCRIPTING",
                "description": "Provide arguments to NSE scripts",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap --script http-title --script-args http.useragent='Custom' 192.168.1.1",
                "complexity": "HARD"
            }, []),
            
            # ========== OUTPUT FORMATS ==========
            ({
                "name": "-oN",
                "category": "OUTPUT",
                "description": "Normal output to file",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -oN scan.txt 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "-oX",
                "category": "OUTPUT",
                "description": "XML output to file",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -oX scan.xml 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "-oG",
                "category": "OUTPUT",
                "description": "Grepable output to file",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -oG scan.gnmap 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "-oA",
                "category": "OUTPUT",
                "description": "Output in all major formats (normal, XML, grepable)",
                "requires_root": False,
                "requires_args": True,
                "example": "nmap -oA scan 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            # ========== MISC OPTIONS ==========
            ({
                "name": "-v",
                "category": "OUTPUT",
                "description": "Increase verbosity level",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -v 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "-d",
                "category": "OUTPUT",
                "description": "Increase debugging level",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -d 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "-A",
                "category": "AGGRESSIVE",
                "description": "Aggressive scan - enables OS detection, version detection, script scanning, and traceroute",
                "requires_root": True,
                "requires_args": False,
                "example": "nmap -A 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "--traceroute",
                "category": "MISC",
                "description": "Trace path to host",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap --traceroute 192.168.1.1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "-6",
                "category": "MISC",
                "description": "Enable IPv6 scanning",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap -6 ::1",
                "complexity": "MEDIUM"
            }, []),
            
            ({
                "name": "--reason",
                "category": "OUTPUT",
                "description": "Display reason for port state",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap --reason 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "--open",
                "category": "OUTPUT",
                "description": "Only show open ports",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap --open 192.168.1.1",
                "complexity": "EASY"
            }, []),
            
            ({
                "name": "--packet-trace",
                "category": "OUTPUT",
                "description": "Show all packets sent and received",
                "requires_root": False,
                "requires_args": False,
                "example": "nmap --packet-trace 192.168.1.1",
                "complexity": "HARD"
            }, []),
        ]
        
        return options
    
    def create_options(self):
        """Create all nmap option nodes in Neo4j."""
        print("\n📝 Creating nmap options...")
        
        options = self.get_nmap_options()
        
        with self.driver.session() as session:
            for option_props, conflicts in options:
                # Create option node
                session.run("""
                    CREATE (o:Option)
                    SET o = $props
                """, props=option_props)
        
        print(f"   ✓ Created {len(options)} option nodes")
        return len(options)
    
    def create_conflict_relationships(self):
        """Create CONFLICTS_WITH relationships between options."""
        print("\n🔗 Creating conflict relationships...")
        
        options = self.get_nmap_options()
        relationship_count = 0
        
        with self.driver.session() as session:
            for option_props, conflicts in options:
                option_name = option_props["name"]
                
                for conflict_name in conflicts:
                    # Create bidirectional conflict relationships
                    session.run("""
                        MATCH (o1:Option {name: $name1})
                        MATCH (o2:Option {name: $name2})
                        MERGE (o1)-[:CONFLICTS_WITH]->(o2)
                    """, name1=option_name, name2=conflict_name)
                    
                    relationship_count += 1
        
        print(f"   ✓ Created {relationship_count} conflict relationships")
        return relationship_count
    
    def verify_data(self):
        """Verify the data was loaded correctly."""
        print("\n✅ Verifying data...")
        
        with self.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (o:Option) RETURN count(o) as count")
            node_count = result.single()["count"]
            print(f"   Options loaded: {node_count}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r:CONFLICTS_WITH]->()
                RETURN count(r) as count
            """)
            rel_count = result.single()["count"]
            print(f"   Conflict relationships: {rel_count}")
            
            # Test a few queries
            print("\n🔍 Sample queries:")
            
            # Scan types
            result = session.run("""
                MATCH (o:Option {category: 'SCAN_TYPE'})
                RETURN o.name as name
                ORDER BY o.name
            """)
            scan_types = [r["name"] for r in result]
            print(f"   Scan types: {', '.join(scan_types[:5])}...")
            
            # Root-required options
            result = session.run("""
                MATCH (o:Option {requires_root: true})
                RETURN count(o) as count
            """)
            root_count = result.single()["count"]
            print(f"   Options requiring root: {root_count}")
            
            # Conflicts for -sS
            result = session.run("""
                MATCH (o:Option {name: '-sS'})-[:CONFLICTS_WITH]->(c:Option)
                RETURN c.name as conflict
                ORDER BY c.name
            """)
            ss_conflicts = [r["conflict"] for r in result]
            print(f"   -sS conflicts with: {', '.join(ss_conflicts[:5])}...")
            
        return node_count, rel_count
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            print("\n👋 Connection closed")
    
    def initialize(self, clear_existing: bool = True):
        """
        Full initialization workflow.
        
        Args:
            clear_existing: Whether to clear existing data first
            
        Returns:
            Tuple of (success, node_count, relationship_count)
        """
        print("=" * 60)
        print("🚀 NMAP KNOWLEDGE GRAPH INITIALIZATION")
        print("=" * 60)
        
        # Connect
        if not self.connect():
            return False, 0, 0
        
        try:
            # Clear existing data
            if clear_existing:
                self.clear_database()
            
            # Create constraints
            self.create_constraints()
            
            # Create nodes
            node_count = self.create_options()
            
            # Create relationships
            rel_count = self.create_conflict_relationships()
            
            # Verify
            verified_nodes, verified_rels = self.verify_data()
            
            print("\n" + "=" * 60)
            print("✅ INITIALIZATION COMPLETE!")
            print("=" * 60)
            print(f"📊 Summary:")
            print(f"   • Options created: {node_count}")
            print(f"   • Conflicts created: {rel_count}")
            print(f"   • Database ready for queries")
            print("=" * 60)
            
            return True, node_count, rel_count
            
        except Exception as e:
            print(f"\n❌ Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            return False, 0, 0
        
        finally:
            self.close()


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize Neo4j Knowledge Graph with nmap options"
    )
    parser.add_argument(
        "--uri",
        default=None,
        help="Neo4j URI (default: from NEO4J_URI env or bolt://localhost:7687)"
    )
    parser.add_argument(
        "--user",
        default=None,
        help="Neo4j username (default: from NEO4J_USER env or neo4j)"
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Neo4j password (default: from NEO4J_PASSWORD env or password123)"
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing data (don't clear database first)"
    )
    
    args = parser.parse_args()
    
    # Initialize
    initializer = KnowledgeGraphInitializer(
        uri=args.uri,
        user=args.user,
        password=args.password
    )
    
    success, nodes, rels = initializer.initialize(
        clear_existing=not args.keep_existing
    )
    
    if success:
        print("\n✅ Knowledge Graph is ready!")
        print("   You can now use the validator with Neo4j integration.")
        sys.exit(0)
    else:
        print("\n❌ Initialization failed!")
        print("   Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()