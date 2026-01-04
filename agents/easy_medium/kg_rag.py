"""
Knowledge Graph RAG - Retrieval Augmented Generation
Module pour interroger le Knowledge Graph NMAP et enrichir les requêtes
"""

from neo4j import GraphDatabase
import re
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NmapKnowledgeGraphRAG:
    """
    RAG pour le Knowledge Graph NMAP
    Interroge Neo4j pour enrichir les requêtes utilisateur
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialise la connexion au Knowledge Graph
        
        Args:
            uri: URI Neo4j (bolt://localhost:7687)
            user: Utilisateur Neo4j
            password: Mot de passe
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"✅ Connecté au Knowledge Graph: {uri}")
    
    def close(self):
        """Ferme la connexion"""
        self.driver.close()
    
    def _run_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Exécute une requête Cypher
        
        Args:
            query: Requête Cypher
            params: Paramètres de la requête
        
        Returns:
            Liste de résultats
        """
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
    
    # ========================================
    # RECHERCHE PAR SERVICE
    # ========================================
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les infos sur un service
        
        Args:
            service_name: Nom du service (HTTP, SSH, FTP...)
        
        Returns:
            Informations sur le service
        """
        query = """
        MATCH (s:Service)
        WHERE toLower(s.name) = toLower($service)
        OPTIONAL MATCH (p:Port)-[:HOSTS]->(s)
        OPTIONAL MATCH (s)-[:USES]->(pr:Protocol)
        RETURN s.name AS service,
               s.category AS category,
               collect(DISTINCT p.number) AS ports,
               collect(DISTINCT p.protocol) AS protocols,
               pr.name AS main_protocol
        """
        
        results = self._run_query(query, {"service": service_name})
        return results[0] if results else None
    
    def search_services_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Cherche des services par mot-clé
        
        Args:
            keyword: Mot-clé (web, mail, remote...)
        
        Returns:
            Liste de services correspondants
        """
        # Mapping de mots-clés
        keyword_map = {
            'web': ['HTTP', 'HTTPS', 'HTTP-Proxy', 'HTTPS-Alt'],
            'mail': ['SMTP', 'POP3', 'IMAP'],
            'email': ['SMTP', 'POP3', 'IMAP'],
            'remote': ['SSH', 'Telnet', 'RDP', 'VNC'],
            'database': ['MySQL', 'PostgreSQL', 'MSSQL', 'MongoDB', 'Redis'],
            'file': ['FTP', 'FTP-Data', 'TFTP', 'SMB'],
            'dns': ['DNS'],
            'snmp': ['SNMP'],
            'telnet': ['Telnet'],
            'ssh': ['SSH'],
            'ftp': ['FTP', 'FTP-Data'],
            'smtp': ['SMTP'],
            'mysql': ['MySQL'],
            'postgres': ['PostgreSQL'],
            'postgresql': ['PostgreSQL'],
        }
        
        keyword_lower = keyword.lower()
        
        # Si mot-clé connu, retourner les services associés
        if keyword_lower in keyword_map:
            services = []
            for service_name in keyword_map[keyword_lower]:
                info = self.get_service_info(service_name)
                if info:
                    services.append(info)
            return services
        
        # Sinon chercher par catégorie
        query = """
        MATCH (s:Service)
        WHERE toLower(s.category) CONTAINS toLower($keyword)
           OR toLower(s.name) CONTAINS toLower($keyword)
        OPTIONAL MATCH (p:Port)-[:HOSTS]->(s)
        RETURN s.name AS service,
               s.category AS category,
               collect(DISTINCT p.number) AS ports
        """
        
        return self._run_query(query, {"keyword": keyword})
    
    # ========================================
    # RECHERCHE PAR PORT
    # ========================================
    
    def get_port_info(self, port_number: int, protocol: str = "TCP") -> Optional[Dict[str, Any]]:
        """
        Récupère les infos sur un port
        
        Args:
            port_number: Numéro de port
            protocol: TCP ou UDP
        
        Returns:
            Informations sur le port
        """
        query = """
        MATCH (p:Port {number: $port, protocol: $protocol})
        OPTIONAL MATCH (p)-[:HOSTS]->(s:Service)
        RETURN p.number AS port,
               p.protocol AS protocol,
               s.name AS service,
               s.category AS category
        """
        
        results = self._run_query(query, {"port": port_number, "protocol": protocol.upper()})
        return results[0] if results else None
    
    def get_common_ports(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les ports communs
        
        Args:
            category: Catégorie optionnelle (Web, Email...)
        
        Returns:
            Liste des ports communs
        """
        if category:
            query = """
            MATCH (p:Port)-[:HOSTS]->(s:Service {category: $category})
            WHERE p.common = true
            RETURN p.number AS port, 
                   p.protocol AS protocol,
                   s.name AS service
            ORDER BY p.number
            """
            return self._run_query(query, {"category": category})
        else:
            query = """
            MATCH (p:Port)-[:HOSTS]->(s:Service)
            WHERE p.common = true
            RETURN p.number AS port,
                   p.protocol AS protocol,
                   s.name AS service
            ORDER BY p.number
            LIMIT 20
            """
            return self._run_query(query)
    
    # ========================================
    # RECHERCHE D'OPTIONS
    # ========================================
    
    def get_scan_options(self, scan_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les options de scan
        
        Args:
            scan_type: Type de scan (SYN, TCP, UDP...)
        
        Returns:
            Liste des options
        """
        if scan_type:
            query = """
            MATCH (st:ScanType)
            WHERE toLower(st.name) CONTAINS toLower($scan_type)
               OR st.flag CONTAINS $scan_type
            RETURN st.flag AS flag,
                   st.name AS name,
                   st.description AS description,
                   st.requires_privileges AS needs_root
            """
            return self._run_query(query, {"scan_type": scan_type})
        else:
            query = """
            MATCH (o:Option)
            WHERE o.category = 'Detection'
            RETURN o.flag AS flag,
                   o.name AS name,
                   o.description AS description
            LIMIT 10
            """
            return self._run_query(query)
    
    def get_conflicting_options(self, flag: str) -> List[str]:
        """
        Récupère les options qui sont en conflit avec un flag
        
        Args:
            flag: Flag nmap (-sS, -sT...)
        
        Returns:
            Liste des flags en conflit
        """
        query = """
        MATCH (o1:Option {flag: $flag})-[:CONFLICTS_WITH]->(o2:Option)
        RETURN o2.flag AS conflicting_flag
        """
        
        results = self._run_query(query, {"flag": flag})
        return [r['conflicting_flag'] for r in results]
    
    def get_complementary_options(self, flag: str) -> List[Dict[str, Any]]:
        """
        Récupère les options complémentaires à un flag
        
        Args:
            flag: Flag nmap
        
        Returns:
            Liste des options complémentaires
        """
        query = """
        MATCH (o1:Option {flag: $flag})-[:COMPLEMENTS]->(o2:Option)
        RETURN o2.flag AS flag,
               o2.name AS name
        """
        
        return self._run_query(query, {"flag": flag})
    
    # ========================================
    # ENRICHISSEMENT DE REQUÊTE
    # ========================================
    
    def enrich_query(self, user_query: str) -> Dict[str, Any]:
        """
        Enrichit une requête utilisateur avec le contexte du Knowledge Graph
        
        Args:
            user_query: Requête en langage naturel
        
        Returns:
            Contexte enrichi pour la génération
        """
        context = {
            'original_query': user_query,
            'services': [],
            'ports': [],
            'scan_types': [],
            'options': [],
            'targets': [],
        }
        
        query_lower = user_query.lower()
        
        # Extraire les services mentionnés
        service_keywords = ['web', 'http', 'https', 'ssh', 'ftp', 'mail', 'smtp', 
                           'database', 'mysql', 'dns', 'remote', 'rdp', 'snmp', 
                           'telnet', 'postgres', 'postgresql', 'mssql', 'mongo',
                           'pop3', 'imap', 'pop', 'vnc', 'rdp']
        
        # D'abord chercher les mots-clés simples
        for keyword in service_keywords:
            if keyword in query_lower:
                services = self.search_services_by_keyword(keyword)
                if services:
                    # Éviter les doublons
                    for svc in services:
                        if svc not in context['services']:
                            context['services'].append(svc)
        
        # Ensuite chercher les noms de services complets
        service_names = ['DNS', 'SNMP', 'Telnet', 'SSH', 'FTP', 'HTTP', 'HTTPS',
                        'SMTP', 'POP3', 'IMAP', 'MySQL', 'PostgreSQL', 'MSSQL']
        
        for svc_name in service_names:
            if svc_name.lower() in query_lower:
                svc_info = self.get_service_info(svc_name)
                if svc_info and svc_info not in context['services']:
                    context['services'].append(svc_info)
        
        # Extraire les ports mentionnés
        port_pattern = r'\b(\d{1,5})\b'
        ports = re.findall(port_pattern, user_query)
        for port_str in ports:
            port_num = int(port_str)
            if 1 <= port_num <= 65535:
                port_info = self.get_port_info(port_num)
                if port_info:
                    context['ports'].append(port_info)
        
        # Extraire les IPs/réseaux
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?\b'
        ips = re.findall(ip_pattern, user_query)
        context['targets'].extend(ips)
        
        # Détecter le type de scan demandé
        scan_keywords = {
            'ping': 'ping',
            'syn': 'SYN',
            'tcp': 'TCP',
            'udp': 'UDP',
            'version': 'version',
            'os': 'OS',
            'aggressive': 'aggressive',
        }
        
        for keyword, scan_type in scan_keywords.items():
            if keyword in query_lower:
                options = self.get_scan_options(scan_type)
                if options:
                    context['scan_types'].extend(options)
        
        # Options recommandées basées sur le contexte
        if 'version' in query_lower or 'service' in query_lower:
            context['options'].append({
                'flag': '-sV',
                'name': 'Version Detection',
                'reason': 'Requested version detection'
            })
        
        if 'os' in query_lower or 'operating system' in query_lower:
            context['options'].append({
                'flag': '-O',
                'name': 'OS Detection',
                'reason': 'Requested OS detection'
            })
        
        return context
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Formate le contexte pour l'inclure dans le prompt T5
        
        Args:
            context: Contexte enrichi
        
        Returns:
            Texte formaté pour le prompt
        """
        parts = []
        
        # Services détectés
        if context['services']:
            services_text = ", ".join([s['service'] for s in context['services']])
            ports_list = []
            for s in context['services']:
                if s.get('ports'):
                    ports_list.extend(s['ports'])
            if ports_list:
                parts.append(f"Services: {services_text} (ports {','.join(map(str, set(ports_list)))})")
        
        # Options recommandées
        if context['options']:
            flags = [o['flag'] for o in context['options']]
            parts.append(f"Recommended flags: {' '.join(flags)}")
        
        # Targets
        if context['targets']:
            parts.append(f"Target: {context['targets'][0]}")
        
        return " | ".join(parts) if parts else ""
    
    # ========================================
    # STATISTIQUES
    # ========================================
    
    def get_stats(self) -> Dict[str, int]:
        """Récupère les statistiques du graphe"""
        stats = {}
        
        # Compter les nœuds
        query = """
        MATCH (n)
        RETURN labels(n)[0] AS type, count(n) AS count
        """
        results = self._run_query(query)
        for r in results:
            stats[r['type']] = r['count']
        
        return stats


# ========================================
# FONCTION HELPER
# ========================================

def create_kg_rag(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "nmap1234"
) -> NmapKnowledgeGraphRAG:
    """
    Crée une instance du RAG
    
    Args:
        uri: URI Neo4j
        user: Utilisateur
        password: Mot de passe
    
    Returns:
        Instance de NmapKnowledgeGraphRAG
    """
    return NmapKnowledgeGraphRAG(uri, user, password)


if __name__ == "__main__":
    """Tests du module RAG"""
    
    # Créer RAG
    rag = create_kg_rag()
    
    print("="*70)
    print("🧪 TESTS DU KNOWLEDGE GRAPH RAG")
    print("="*70)
    
    # Test 1: Info sur SSH
    print("\n1️⃣ Test: Informations sur SSH")
    ssh_info = rag.get_service_info("SSH")
    print(f"   Service: {ssh_info['service']}")
    print(f"   Ports: {ssh_info['ports']}")
    print(f"   Protocole: {ssh_info['main_protocol']}")
    
    # Test 2: Recherche par mot-clé
    print("\n2️⃣ Test: Recherche services 'web'")
    web_services = rag.search_services_by_keyword('web')
    for svc in web_services:
        print(f"   {svc['service']:15s} - Ports: {svc['ports']}")
    
    # Test 3: Info sur port
    print("\n3️⃣ Test: Informations sur port 80")
    port_info = rag.get_port_info(80)
    print(f"   Port: {port_info['port']}")
    print(f"   Service: {port_info['service']}")
    print(f"   Catégorie: {port_info['category']}")
    
    # Test 4: Enrichissement de requête
    print("\n4️⃣ Test: Enrichissement de requête")
    test_query = "scan for web servers on 192.168.1.0/24"
    context = rag.enrich_query(test_query)
    print(f"   Requête: {test_query}")
    print(f"   Services détectés: {[s['service'] for s in context['services']]}")
    print(f"   Targets: {context['targets']}")
    formatted = rag.format_context_for_prompt(context)
    print(f"   Contexte formaté: {formatted}")
    
    # Test 5: Options complémentaires
    print("\n5️⃣ Test: Options complémentaires à -sV")
    complements = rag.get_complementary_options('-sV')
    for opt in complements:
        print(f"   {opt['flag']:10s} - {opt['name']}")
    
    # Stats
    print("\n📊 Statistiques:")
    stats = rag.get_stats()
    for node_type, count in stats.items():
        print(f"   {node_type:15s}: {count:3d} nœuds")
    
    print("="*70)
    print("✅ Tests terminés !")
    
    rag.close()