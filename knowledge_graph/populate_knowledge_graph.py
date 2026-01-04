"""
NMAP Knowledge Graph - Population Script
Crée et peuple le graphe de connaissances NMAP dans Neo4j
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NmapKnowledgeGraphBuilder:
    """Construit et peuple le Knowledge Graph NMAP dans Neo4j"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connecté à Neo4j : {uri}")
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Supprime toutes les données (pour recommencer à zéro)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("✅ Base de données nettoyée")
    
    def create_constraints(self):
        """Crée les contraintes d'unicité"""
        constraints = [
            "CREATE CONSTRAINT port_combo IF NOT EXISTS FOR (p:Port) REQUIRE (p.number, p.protocol) IS UNIQUE",
            "CREATE CONSTRAINT service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT protocol_name IF NOT EXISTS FOR (p:Protocol) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT scantype_flag IF NOT EXISTS FOR (st:ScanType) REQUIRE st.flag IS UNIQUE",
            "CREATE CONSTRAINT option_flag IF NOT EXISTS FOR (o:Option) REQUIRE o.flag IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ Contrainte créée")
                except Exception as e:
                    logger.warning(f"Contrainte existe déjà")
    
    def create_indexes(self):
        """Crée les index pour la performance"""
        indexes = [
            "CREATE INDEX port_protocol IF NOT EXISTS FOR (p:Port) ON (p.protocol)",
            "CREATE INDEX service_category IF NOT EXISTS FOR (s:Service) ON (s.category)",
            "CREATE INDEX option_category IF NOT EXISTS FOR (o:Option) ON (o.category)",
        ]
        
        with self.driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"✅ Index créé")
                except Exception as e:
                    logger.warning(f"Index existe déjà")
    
    def create_protocols(self):
        """Crée les nœuds Protocol"""
        protocols = [
            {"name": "TCP", "layer": 4, "description": "Transmission Control Protocol"},
            {"name": "UDP", "layer": 4, "description": "User Datagram Protocol"},
            {"name": "ICMP", "layer": 3, "description": "Internet Control Message Protocol"},
            {"name": "SCTP", "layer": 4, "description": "Stream Control Transmission Protocol"},
        ]
        
        with self.driver.session() as session:
            for proto in protocols:
                session.run("""
                    MERGE (p:Protocol {name: $name})
                    SET p.layer = $layer, p.description = $description
                """, **proto)
            logger.info(f"✅ {len(protocols)} protocoles créés")
    
    def create_ports_and_services(self):
        """Crée les nœuds Port et Service avec leurs relations"""
        
        # Données : Port → Service
        ports_services = [
            # Web
            {"port": 80, "protocol": "TCP", "service": "HTTP", "category": "Web", "common": True},
            {"port": 443, "protocol": "TCP", "service": "HTTPS", "category": "Web", "common": True},
            {"port": 8080, "protocol": "TCP", "service": "HTTP-Proxy", "category": "Web", "common": True},
            {"port": 8443, "protocol": "TCP", "service": "HTTPS-Alt", "category": "Web", "common": True},
            
            # Remote Access
            {"port": 22, "protocol": "TCP", "service": "SSH", "category": "Remote Access", "common": True},
            {"port": 23, "protocol": "TCP", "service": "Telnet", "category": "Remote Access", "common": True},
            {"port": 3389, "protocol": "TCP", "service": "RDP", "category": "Remote Access", "common": True},
            {"port": 5900, "protocol": "TCP", "service": "VNC", "category": "Remote Access", "common": False},
            
            # File Transfer
            {"port": 21, "protocol": "TCP", "service": "FTP", "category": "File Transfer", "common": True},
            {"port": 20, "protocol": "TCP", "service": "FTP-Data", "category": "File Transfer", "common": True},
            {"port": 69, "protocol": "UDP", "service": "TFTP", "category": "File Transfer", "common": False},
            {"port": 445, "protocol": "TCP", "service": "SMB", "category": "File Transfer", "common": True},
            
            # Email
            {"port": 25, "protocol": "TCP", "service": "SMTP", "category": "Email", "common": True},
            {"port": 110, "protocol": "TCP", "service": "POP3", "category": "Email", "common": True},
            {"port": 143, "protocol": "TCP", "service": "IMAP", "category": "Email", "common": True},
            {"port": 587, "protocol": "TCP", "service": "SMTP-Submission", "category": "Email", "common": True},
            
            # DNS
            {"port": 53, "protocol": "TCP", "service": "DNS", "category": "Infrastructure", "common": True},
            {"port": 53, "protocol": "UDP", "service": "DNS", "category": "Infrastructure", "common": True},
            
            # Database
            {"port": 3306, "protocol": "TCP", "service": "MySQL", "category": "Database", "common": True},
            {"port": 5432, "protocol": "TCP", "service": "PostgreSQL", "category": "Database", "common": True},
            {"port": 1433, "protocol": "TCP", "service": "MSSQL", "category": "Database", "common": True},
            {"port": 27017, "protocol": "TCP", "service": "MongoDB", "category": "Database", "common": False},
            {"port": 6379, "protocol": "TCP", "service": "Redis", "category": "Database", "common": False},
            
            # Monitoring/Management
            {"port": 161, "protocol": "UDP", "service": "SNMP", "category": "Monitoring", "common": True},
            {"port": 162, "protocol": "UDP", "service": "SNMP-Trap", "category": "Monitoring", "common": False},
        ]
        
        with self.driver.session() as session:
            for ps in ports_services:
                # Créer Port
                session.run("""
                    MERGE (p:Port {number: $port, protocol: $protocol})
                    SET p.service_name = $service,
                        p.description = $service + ' service',
                        p.common = $common
                """, port=ps["port"], protocol=ps["protocol"], 
                     service=ps["service"], common=ps["common"])
                
                # Créer Service
                session.run("""
                    MERGE (s:Service {name: $service})
                    SET s.category = $category,
                        s.description = $service + ' service'
                """, service=ps["service"], category=ps["category"])
                
                # Créer relation Port-[:HOSTS]->Service
                session.run("""
                    MATCH (p:Port {number: $port, protocol: $protocol})
                    MATCH (s:Service {name: $service})
                    MERGE (p)-[:HOSTS {default: true}]->(s)
                """, port=ps["port"], protocol=ps["protocol"], service=ps["service"])
                
                # Créer relation Service-[:USES]->Protocol
                session.run("""
                    MATCH (s:Service {name: $service})
                    MATCH (pr:Protocol {name: $protocol})
                    MERGE (s)-[:USES]->(pr)
                """, service=ps["service"], protocol=ps["protocol"])
            
            logger.info(f"✅ {len(ports_services)} ports et services créés")
    
    def create_scan_types(self):
        """Crée les types de scan NMAP"""
        scan_types = [
            {
                "name": "SYN Scan",
                "flag": "-sS",
                "description": "TCP SYN/Half-open scan (stealth)",
                "stealth": True,
                "requires_privileges": True,
                "speed": "Fast",
                "reliability": "High"
            },
            {
                "name": "TCP Connect Scan",
                "flag": "-sT",
                "description": "Full TCP connection scan",
                "stealth": False,
                "requires_privileges": False,
                "speed": "Normal",
                "reliability": "High"
            },
            {
                "name": "UDP Scan",
                "flag": "-sU",
                "description": "UDP port scan",
                "stealth": False,
                "requires_privileges": True,
                "speed": "Slow",
                "reliability": "Medium"
            },
            {
                "name": "Ping Scan",
                "flag": "-sn",
                "description": "Host discovery only (no port scan)",
                "stealth": False,
                "requires_privileges": False,
                "speed": "Fast",
                "reliability": "High"
            },
            {
                "name": "ACK Scan",
                "flag": "-sA",
                "description": "TCP ACK scan for firewall detection",
                "stealth": True,
                "requires_privileges": True,
                "speed": "Fast",
                "reliability": "Medium"
            },
            {
                "name": "FIN Scan",
                "flag": "-sF",
                "description": "TCP FIN scan (stealth)",
                "stealth": True,
                "requires_privileges": False,
                "speed": "Fast",
                "reliability": "Medium"
            },
        ]
        
        with self.driver.session() as session:
            for st in scan_types:
                session.run("""
                    MERGE (st:ScanType {flag: $flag})
                    SET st.name = $name,
                        st.description = $description,
                        st.stealth = $stealth,
                        st.requires_privileges = $requires_privileges,
                        st.speed = $speed,
                        st.reliability = $reliability
                """, **st)
            logger.info(f"✅ {len(scan_types)} types de scan créés")
    
    def create_options(self):
        """Crée les options/flags NMAP"""
        options = [
            {
                "flag": "-p",
                "name": "Port Specification",
                "description": "Specify ports to scan",
                "category": "Target",
                "requires_privileges": False,
                "impact_performance": "Low"
            },
            {
                "flag": "-sV",
                "name": "Version Detection",
                "description": "Probe open ports to determine service/version info",
                "category": "Detection",
                "requires_privileges": False,
                "impact_performance": "Medium"
            },
            {
                "flag": "-O",
                "name": "OS Detection",
                "description": "Enable OS detection",
                "category": "Detection",
                "requires_privileges": True,
                "impact_performance": "Medium"
            },
            {
                "flag": "-A",
                "name": "Aggressive Scan",
                "description": "Enable OS detection, version detection, script scanning, and traceroute",
                "category": "Detection",
                "requires_privileges": True,
                "impact_performance": "High"
            },
            {
                "flag": "-T4",
                "name": "Timing Template (Aggressive)",
                "description": "Faster scan timing",
                "category": "Performance",
                "requires_privileges": False,
                "impact_performance": "Low"
            },
            {
                "flag": "-T5",
                "name": "Timing Template (Insane)",
                "description": "Fastest scan timing",
                "category": "Performance",
                "requires_privileges": False,
                "impact_performance": "Low"
            },
            {
                "flag": "-Pn",
                "name": "Skip Ping",
                "description": "Treat all hosts as online (skip host discovery)",
                "category": "Discovery",
                "requires_privileges": False,
                "impact_performance": "Low"
            },
            {
                "flag": "--traceroute",
                "name": "Traceroute",
                "description": "Trace hop path to each host",
                "category": "Discovery",
                "requires_privileges": False,
                "impact_performance": "Medium"
            },
            {
                "flag": "-sC",
                "name": "Default Scripts",
                "description": "Run default NSE scripts",
                "category": "Detection",
                "requires_privileges": False,
                "impact_performance": "High"
            },
            {
                "flag": "--script",
                "name": "Custom Scripts",
                "description": "Run specified NSE scripts",
                "category": "Detection",
                "requires_privileges": False,
                "impact_performance": "High"
            },
        ]
        
        with self.driver.session() as session:
            for opt in options:
                session.run("""
                    MERGE (o:Option {flag: $flag})
                    SET o.name = $name,
                        o.description = $description,
                        o.category = $category,
                        o.requires_privileges = $requires_privileges,
                        o.impact_performance = $impact_performance
                """, **opt)
            logger.info(f"✅ {len(options)} options créées")
    
    def create_option_relations(self):
        """Crée les relations entre options (conflits, compléments)"""
        
        # Conflits
        conflicts = [
            ("-sS", "-sT", "Cannot use both SYN and TCP Connect scans"),
            ("-sS", "-sU", "Different scan types - use separately"),
            ("-T4", "-T5", "Choose only one timing template"),
        ]
        
        with self.driver.session() as session:
            for flag1, flag2, reason in conflicts:
                session.run("""
                    MATCH (o1:Option {flag: $flag1})
                    MATCH (o2:Option {flag: $flag2})
                    MERGE (o1)-[:CONFLICTS_WITH {reason: $reason}]->(o2)
                """, flag1=flag1, flag2=flag2, reason=reason)
            logger.info(f"✅ {len(conflicts)} conflits créés")
        
        # Compléments
        complements = [
            ("-sV", "-sC", "Version detection works well with scripts"),
            ("-O", "-sV", "OS and version detection complement each other"),
            ("-A", "-T4", "Aggressive scan benefits from faster timing"),
        ]
        
        with self.driver.session() as session:
            for flag1, flag2, synergy in complements:
                session.run("""
                    MATCH (o1:Option {flag: $flag1})
                    MATCH (o2:Option {flag: $flag2})
                    MERGE (o1)-[:COMPLEMENTS {synergy: $synergy}]->(o2)
                """, flag1=flag1, flag2=flag2, synergy=synergy)
            logger.info(f"✅ {len(complements)} compléments créés")
    
    def create_os_fingerprints(self):
        """Crée les signatures d'OS"""
        os_fingerprints = [
            {"name": "Linux 3.x-4.x", "os_family": "Linux", "version": "3.x-4.x", "reliability": 95},
            {"name": "Linux 5.x", "os_family": "Linux", "version": "5.x", "reliability": 98},
            {"name": "Windows 10", "os_family": "Windows", "version": "10", "reliability": 97},
            {"name": "Windows Server 2019", "os_family": "Windows", "version": "2019", "reliability": 96},
            {"name": "FreeBSD 11.x-12.x", "os_family": "BSD", "version": "11.x-12.x", "reliability": 90},
            {"name": "macOS 10.15-11.x", "os_family": "macOS", "version": "10.15-11.x", "reliability": 93},
        ]
        
        with self.driver.session() as session:
            for os in os_fingerprints:
                session.run("""
                    MERGE (os:OSFingerprint {name: $name})
                    SET os.os_family = $os_family,
                        os.version = $version,
                        os.reliability = $reliability
                """, **os)
            
            # Relation ScanType-[:IDENTIFIES]->OSFingerprint
            session.run("""
                MATCH (st:ScanType {flag: "-O"})
                MATCH (os:OSFingerprint)
                MERGE (st)-[:IDENTIFIES {confidence: os.reliability}]->(os)
            """)
            
            logger.info(f"✅ {len(os_fingerprints)} signatures OS créées")
    
    def build_full_graph(self, clear_first=True):
        """Construit le graphe complet"""
        logger.info("🚀 Construction du Knowledge Graph NMAP...")
        
        if clear_first:
            logger.info("🧹 Nettoyage de la base...")
            self.clear_database()
        
        logger.info("📋 Création des contraintes...")
        self.create_constraints()
        
        logger.info("🔍 Création des index...")
        self.create_indexes()
        
        logger.info("🌐 Création des protocoles...")
        self.create_protocols()
        
        logger.info("🔌 Création des ports et services...")
        self.create_ports_and_services()
        
        logger.info("🔎 Création des types de scan...")
        self.create_scan_types()
        
        logger.info("⚙️ Création des options...")
        self.create_options()
        
        logger.info("🔗 Création des relations entre options...")
        self.create_option_relations()
        
        logger.info("💻 Création des signatures OS...")
        self.create_os_fingerprints()
        
        logger.info("✅ Knowledge Graph NMAP créé avec succès !")
    
    def get_stats(self):
        """Affiche les statistiques du graphe"""
        with self.driver.session() as session:
            # Compter les nœuds par type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] AS type, count(n) AS count
                ORDER BY count DESC
            """)
            
            print("\n📊 Statistiques du Knowledge Graph:")
            print("="*50)
            for record in result:
                print(f"   {record['type']:20s}: {record['count']:4d} nœuds")
            
            # Compter les relations
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS relation_type, count(r) AS count
                ORDER BY count DESC
            """)
            
            print("\n🔗 Relations:")
            print("="*50)
            for record in result:
                print(f"   {record['relation_type']:20s}: {record['count']:4d} relations")
            
            print("="*50)


if __name__ == "__main__":
    # Configuration
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "nmap1234"
    
    # Créer le builder
    builder = NmapKnowledgeGraphBuilder(URI, USER, PASSWORD)
    
    try:
        # Construire le graphe complet
        builder.build_full_graph(clear_first=True)
        
        # Afficher les stats
        builder.get_stats()
        
    finally:
        builder.close()
    
    print("\n✅ Script terminé !")
    print("\n💡 Ouvre http://localhost:7474 pour visualiser le graphe")
    print("   Essaie cette requête : MATCH (n) RETURN n LIMIT 50")