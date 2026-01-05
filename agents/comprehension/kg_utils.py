"""
Knowledge Graph Utilities
Provides interface to Neo4j for nmap option querying and validation.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import os


@dataclass
class NmapOption:
    """Represents an nmap option/flag."""
    name: str
    category: str
    description: str
    requires_root: bool
    requires_args: bool
    conflicts_with: List[str]
    example: str


class Neo4jClient:
    """Singleton client for Neo4j Knowledge Graph queries."""
    
    # _instance = None
    
    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #         cls._instance._initialized = False
    #     return cls._instance
    
    # def __init__(self):
    #     if self._initialized:
    #         return
            
    #     self._initialized = True
    #     self.driver = None
    #     self._connect()

    def __init__(self):
        """Initialize Neo4j client with current environment variables."""
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Connect to Neo4j database."""
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password123")
            
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            print(f"✓ Connected to Neo4j at {uri}")
            
        except Exception as e:
            print(f"⚠ Neo4j connection failed: {e}")
            print("  Using in-memory fallback data")
            self.driver = None
            self._init_fallback_data()
    
    def _init_fallback_data(self):
        """Initialize fallback in-memory data when Neo4j is unavailable."""
        self.fallback_options = {
            # Scan Types
            "-sS": NmapOption(
                name="-sS",
                category="SCAN_TYPE",
                description="TCP SYN scan (stealth scan)",
                requires_root=True,
                requires_args=False,
                conflicts_with=["-sT", "-sU", "-sn"],
                example="nmap -sS 192.168.1.1"
            ),
            "-sT": NmapOption(
                name="-sT",
                category="SCAN_TYPE",
                description="TCP connect scan",
                requires_root=False,
                requires_args=False,
                conflicts_with=["-sS", "-sU", "-sn"],
                example="nmap -sT 192.168.1.1"
            ),
            "-sU": NmapOption(
                name="-sU",
                category="SCAN_TYPE",
                description="UDP scan",
                requires_root=True,
                requires_args=False,
                conflicts_with=["-sS", "-sT", "-sn"],
                example="nmap -sU 192.168.1.1"
            ),
            "-sn": NmapOption(
                name="-sn",
                category="DISCOVERY",
                description="Ping scan (no port scan)",
                requires_root=False,
                requires_args=False,
                conflicts_with=["-sS", "-sT", "-sU", "-p"],
                example="nmap -sn 192.168.1.0/24"
            ),
            
            # Port Specification
            "-p": NmapOption(
                name="-p",
                category="PORT_SPEC",
                description="Port specification",
                requires_root=False,
                requires_args=True,
                conflicts_with=["-F"],
                example="nmap -p 80,443 192.168.1.1"
            ),
            "-p-": NmapOption(
                name="-p-",
                category="PORT_SPEC",
                description="Scan all 65535 ports",
                requires_root=False,
                requires_args=False,
                conflicts_with=["-F", "--top-ports"],
                example="nmap -p- 192.168.1.1"
            ),
            "-F": NmapOption(
                name="-F",
                category="PORT_SPEC",
                description="Fast scan (100 common ports)",
                requires_root=False,
                requires_args=False,
                conflicts_with=["-p", "-p-"],
                example="nmap -F 192.168.1.1"
            ),
            "--top-ports": NmapOption(
                name="--top-ports",
                category="PORT_SPEC",
                description="Scan N most common ports",
                requires_root=False,
                requires_args=True,
                conflicts_with=["-p-"],
                example="nmap --top-ports 10 192.168.1.1"
            ),
            
            # Service/Version Detection
            "-sV": NmapOption(
                name="-sV",
                category="SERVICE_DETECTION",
                description="Version detection",
                requires_root=False,
                requires_args=False,
                conflicts_with=[],
                example="nmap -sV 192.168.1.1"
            ),
            
            # OS Detection
            "-O": NmapOption(
                name="-O",
                category="OS_DETECTION",
                description="OS detection",
                requires_root=True,
                requires_args=False,
                conflicts_with=[],
                example="nmap -O 192.168.1.1"
            ),
            
            # Timing
            "-T0": NmapOption(name="-T0", category="TIMING", description="Paranoid timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T1","-T2","-T3","-T4","-T5"], 
                            example="nmap -T0 192.168.1.1"),
            "-T1": NmapOption(name="-T1", category="TIMING", description="Sneaky timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T0","-T2","-T3","-T4","-T5"], 
                            example="nmap -T1 192.168.1.1"),
            "-T2": NmapOption(name="-T2", category="TIMING", description="Polite timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T0","-T1","-T3","-T4","-T5"], 
                            example="nmap -T2 192.168.1.1"),
            "-T3": NmapOption(name="-T3", category="TIMING", description="Normal timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T0","-T1","-T2","-T4","-T5"], 
                            example="nmap -T3 192.168.1.1"),
            "-T4": NmapOption(name="-T4", category="TIMING", description="Aggressive timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T0","-T1","-T2","-T3","-T5"], 
                            example="nmap -T4 192.168.1.1"),
            "-T5": NmapOption(name="-T5", category="TIMING", description="Insane timing", 
                            requires_root=False, requires_args=False, conflicts_with=["-T0","-T1","-T2","-T3","-T4"], 
                            example="nmap -T5 192.168.1.1"),
            
            # Scripts
            "--script": NmapOption(
                name="--script",
                category="SCRIPTING",
                description="Run NSE scripts",
                requires_root=False,
                requires_args=True,
                conflicts_with=[],
                example="nmap --script vuln 192.168.1.1"
            ),
            
            # Output
            "-oX": NmapOption(name="-oX", category="OUTPUT", description="XML output", 
                            requires_root=False, requires_args=True, conflicts_with=[], 
                            example="nmap -oX scan.xml 192.168.1.1"),
            "-oN": NmapOption(name="-oN", category="OUTPUT", description="Normal output", 
                            requires_root=False, requires_args=True, conflicts_with=[], 
                            example="nmap -oN scan.txt 192.168.1.1"),
            "-oG": NmapOption(name="-oG", category="OUTPUT", description="Grepable output", 
                            requires_root=False, requires_args=True, conflicts_with=[], 
                            example="nmap -oG scan.gnmap 192.168.1.1"),
            
            # Other
            "--traceroute": NmapOption(
                name="--traceroute",
                category="MISC",
                description="Trace path to host",
                requires_root=False,
                requires_args=False,
                conflicts_with=[],
                example="nmap --traceroute 192.168.1.1"
            ),
            "-6": NmapOption(
                name="-6",
                category="MISC",
                description="IPv6 scanning",
                requires_root=False,
                requires_args=False,
                conflicts_with=[],
                example="nmap -6 ::1"
            ),
            "-A": NmapOption(
                name="-A",
                category="AGGRESSIVE",
                description="Aggressive scan (OS, version, scripts, traceroute)",
                requires_root=True,
                requires_args=False,
                conflicts_with=[],
                example="nmap -A 192.168.1.1"
            ),
            "-v": NmapOption(
                name="-v",
                category="OUTPUT",
                description="Verbose output",
                requires_root=False,
                requires_args=False,
                conflicts_with=[],
                example="nmap -v 192.168.1.1"
            ),
            "-Pn": NmapOption(
                name="-Pn",
                category="HOST_DISCOVERY",
                description="Skip host discovery",
                requires_root=False,
                requires_args=False,
                conflicts_with=["-sn"],
                example="nmap -Pn 192.168.1.1"
            ),
        }
        
        print(f"✓ Loaded {len(self.fallback_options)} nmap options (fallback mode)")
    
    def get_options(
        self,
        requires_root: Optional[bool] = None,
        category: Optional[str] = None,
        exclude_conflicts: Optional[List[str]] = None
    ) -> List[NmapOption]:
        """
        Query nmap options from Knowledge Graph.
        
        Args:
            requires_root: Filter by root requirement (None = no filter)
            category: Filter by category (None = no filter)
            exclude_conflicts: Exclude options that conflict with these
            
        Returns:
            List of matching NmapOption objects
        """
        if self.driver:
            return self._get_options_neo4j(requires_root, category, exclude_conflicts)
        else:
            return self._get_options_fallback(requires_root, category, exclude_conflicts)
    
    def _get_options_neo4j(
        self,
        requires_root: Optional[bool],
        category: Optional[str],
        exclude_conflicts: Optional[List[str]]
    ) -> List[NmapOption]:
        """Query from Neo4j."""
        with self.driver.session() as session:
            query = "MATCH (o:Option) "
            conditions = []
            params = {}
            
            if requires_root is not None:
                conditions.append("o.requires_root = $requires_root")
                params["requires_root"] = requires_root
            
            if category:
                conditions.append("o.category = $category")
                params["category"] = category
            
            if conditions:
                query += "WHERE " + " AND ".join(conditions) + " "
            
            query += """
            OPTIONAL MATCH (o)-[:CONFLICTS_WITH]->(c:Option)
            RETURN o.name as name, o.category as category, 
                   o.description as description, o.requires_root as requires_root,
                   o.requires_args as requires_args, o.example as example,
                   collect(c.name) as conflicts
            """
            
            result = session.run(query, params)
            
            options = []
            for record in result:
                conflicts = [c for c in record["conflicts"] if c]
                
                # Filter out conflicting options
                if exclude_conflicts:
                    if any(c in exclude_conflicts for c in conflicts):
                        continue
                
                options.append(NmapOption(
                    name=record["name"],
                    category=record["category"],
                    description=record["description"],
                    requires_root=record["requires_root"],
                    requires_args=record["requires_args"],
                    conflicts_with=conflicts,
                    example=record["example"]
                ))
            
            return options
    
    def _get_options_fallback(
        self,
        requires_root: Optional[bool],
        category: Optional[str],
        exclude_conflicts: Optional[List[str]]
    ) -> List[NmapOption]:
        """Query from fallback data."""
        options = list(self.fallback_options.values())
        
        # Apply filters
        if requires_root is not None:
            options = [o for o in options if o.requires_root == requires_root]
        
        if category:
            options = [o for o in options if o.category == category]
        
        if exclude_conflicts:
            options = [
                o for o in options
                if not any(c in exclude_conflicts for c in o.conflicts_with)
            ]
        
        return options
    
    def get_conflicts(self, option: str) -> List[str]:
        """
        Get list of options that conflict with the given option.
        
        Args:
            option: Nmap option (e.g., "-sS")
            
        Returns:
            List of conflicting option names
        """
        if self.driver:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (o:Option {name: $option})-[:CONFLICTS_WITH]->(c:Option)
                    RETURN c.name as conflict
                    """,
                    option=option
                )
                return [record["conflict"] for record in result]
        else:
            if option in self.fallback_options:
                return self.fallback_options[option].conflicts_with
            return []
    
    def validate_command_conflicts(self, flags: List[str]) -> Dict[str, List[str]]:
        """
        Check for conflicts in a list of flags.
        
        Args:
            flags: List of nmap flags
            
        Returns:
            Dict mapping each conflicting flag to its conflicts found in the command
        """
        conflicts_found = {}
        flag_set = set(flags)
        
        for flag in flags:
            conflicts = self.get_conflicts(flag)
            found_conflicts = [c for c in conflicts if c in flag_set]
            if found_conflicts:
                conflicts_found[flag] = found_conflicts
        
        return conflicts_found
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()


# Singleton instance
# _kg_client = None

# def get_kg_client() -> Neo4jClient:
#     """Get or create the KG client singleton."""
#     global _kg_client
#     if _kg_client is None:
#         _kg_client = Neo4jClient()
#     return _kg_client


def get_kg_client() -> Neo4jClient:
    """
    Create a fresh Neo4j Knowledge Graph client.
    
    Creates a new client instance to ensure environment variables
    are read fresh (important for testing with different configs).
    
    Returns:
        Neo4jClient: Knowledge graph client instance
    """
    return Neo4jClient()


@dataclass
class Port:
    """Represents a port/service."""
    number: int
    service: str
    protocol: str
    description: str


def get_options(
    category: Optional[str] = None,
    requires_root: Optional[bool] = None,
    complexity: Optional[str] = None,
    max_complexity: Optional[str] = None,
    exclude_conflicts: Optional[List[str]] = None
) -> List[NmapOption]:
    """Get nmap options from Knowledge Graph."""
    client = get_kg_client()
    options = client.get_options(
        requires_root=requires_root,
        category=category,
        exclude_conflicts=exclude_conflicts
    )
    
    # Complexity filtering
    complexity_map = {
        'SCAN_TYPE': 'EASY',
        'DISCOVERY': 'EASY',
        'PORT_SPEC': 'EASY',
        'SERVICE_DETECTION': 'MEDIUM',
        'OS_DETECTION': 'MEDIUM',
        'TIMING': 'MEDIUM',
        'SCRIPTING': 'HARD',
        'AGGRESSIVE': 'HARD',
        'MISC': 'EASY',
        'OUTPUT': 'EASY',
        'HOST_DISCOVERY': 'MEDIUM'
    }
    
    if complexity:
        options = [o for o in options if complexity_map.get(o.category, 'MEDIUM') == complexity]
    
    if max_complexity:
        level_order = {'EASY': 0, 'MEDIUM': 1, 'HARD': 2}
        max_level = level_order.get(max_complexity, 2)
        options = [
            o for o in options 
            if level_order.get(complexity_map.get(o.category, 'MEDIUM'), 1) <= max_level
        ]
    
    return options


def get_conflicts(option: str) -> List[str]:
    """Get list of options that conflict with the given option."""
    client = get_kg_client()
    return client.get_conflicts(option)


def get_port_info(port: Optional[int] = None, service: Optional[str] = None) -> Port:
    """Get port information by number or service name."""
    PORTS = {
        21: Port(21, "FTP", "TCP", "File Transfer Protocol"),
        22: Port(22, "SSH", "TCP", "Secure Shell"),
        23: Port(23, "Telnet", "TCP", "Telnet"),
        25: Port(25, "SMTP", "TCP", "Simple Mail Transfer Protocol"),
        53: Port(53, "DNS", "TCP/UDP", "Domain Name System"),
        80: Port(80, "HTTP", "TCP", "Hypertext Transfer Protocol"),
        443: Port(443, "HTTPS", "TCP", "HTTP Secure"),
        161: Port(161, "SNMP", "UDP", "Simple Network Management Protocol"),
        3306: Port(3306, "MySQL", "TCP", "MySQL Database"),
        3389: Port(3389, "RDP", "TCP", "Remote Desktop Protocol"),
    }
    
    if port is not None:
        if port in PORTS:
            return PORTS[port]
        raise ValueError(f"Port {port} not found")
    
    if service is not None:
        service_upper = service.upper()
        for p in PORTS.values():
            if p.service.upper() == service_upper:
                return p
        raise ValueError(f"Service '{service}' not found")
    
    raise ValueError("Must provide either port or service")


def validate_command_conflicts(flags: List[str]) -> Dict[str, List[str]]:
    """Check for conflicts in a list of flags."""
    client = get_kg_client()
    return client.validate_command_conflicts(flags)






# reasons why I changed the original code :
# problems faced :
# ### **❌ AVANT (avec double singleton):**
# ```
# 1er appel → Neo4jClient() → __new__ crée instance → __init__ lit env vars (password="password")
#                             ↓
#                          Instance cachée
#                             ↓
# 2e appel → Neo4jClient() → __new__ retourne instance cachée → __init__ skip (already initialized)
#                             ↓
#                     Toujours le vieux password!
# ```

# ### **✅ APRÈS (sans singleton):**
# ```
# Chaque appel → Neo4jClient() → __init__ lit env vars FRAIS
#                                 ↓
#                          Nouvelles credentials!