"""
Advanced Post-Processor pour NMAP-AI
Reconstruit complètement la commande à partir du contexte KG
"""

import re
from typing import Dict, List, Optional


class AdvancedNmapPostProcessor:
    """
    Post-processor avancé qui reconstruit la commande nmap
    au lieu de simplement corriger
    """
    
    def __init__(self, kg_context: Dict = None):
        self.context = kg_context or {}
    
    def process(self, raw_command: str, query: str) -> str:
        """
        Traite la commande en la reconstruisant si nécessaire
        
        Args:
            raw_command: Commande brute de T5
            query: Requête originale de l'utilisateur
        
        Returns:
            Commande corrigée ou reconstruite
        """
        # 1. Parser la commande brute
        parsed = self._parse_command(raw_command)
        
        # 2. Détecter les intentions de la requête
        intentions = self._detect_intentions(query)
        
        # 3. Décider : corriger ou reconstruire ?
        if self._needs_reconstruction(parsed, intentions):
            return self._rebuild_from_context(intentions)
        else:
            return self._fix_command(parsed, intentions)
    
    def _parse_command(self, command: str) -> Dict:
        """Parse une commande nmap"""
        parts = command.split()
        
        parsed = {
            'scan_type': None,
            'ports': [],
            'options': [],
            'targets': [],
            'raw_parts': parts
        }
        
        i = 1 if parts and parts[0] == 'nmap' else 0
        
        while i < len(parts):
            part = parts[i]
            
            # Scan types
            if part in {'-sS', '-sT', '-sU', '-sn', '-sA'}:
                parsed['scan_type'] = part
            
            # Bug T5: -sO devrait être -O
            elif part == '-sO':
                parsed['options'].append('-O')
            
            # Ports
            elif part == '-p':
                if i + 1 < len(parts):
                    parsed['ports'].append(parts[i + 1])
                    i += 1
            elif part == '-p-':
                parsed['ports'].append('-')
            
            # Options
            elif part in {'-sV', '-O', '-A', '-sC', '-T4', '-T3', '-T2'}:
                parsed['options'].append(part)
            
            # Targets (IP ou CIDR)
            elif self._is_target(part):
                parsed['targets'].append(part)
            
            i += 1
        
        return parsed
    
    def _is_target(self, token: str) -> bool:
        """Vérifie si c'est une target valide"""
        # IP
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', token):
            return True
        # CIDR
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', token):
            return True
        return False
    
    def _detect_intentions(self, query: str) -> Dict:
        """Détecte les intentions de la requête"""
        q = query.lower()
        
        return {
            'ping_scan': any(kw in q for kw in ['ping scan', 'host discovery']),
            'all_ports': any(kw in q for kw in ['all ports', 'full port', 'scan all', 'complete scan', 'entire port']),
            'os_detect': any(kw in q for kw in ['os detect', 'operating system', 'fingerprint']),
            'aggressive': 'aggressive' in q,
            'scripts': 'script' in q,
            'fast': 'fast' in q or 'quick' in q,
        }
    
    def _needs_reconstruction(self, parsed: Dict, intentions: Dict) -> bool:
        """Détermine si on doit reconstruire complètement"""
        
        # Si ping scan + ports → reconstruction
        if parsed['scan_type'] == '-sn' and parsed['ports']:
            return True
        
        # Si all_ports demandé → reconstruction
        if intentions['all_ports']:
            return True
        
        # Si services du contexte mais pas de ports corrects
        if self.context.get('services') and not self._has_correct_ports(parsed):
            return True
        
        # Si intentions claires mais commande incorrecte
        if intentions['aggressive'] and '-A' not in parsed['options']:
            return True
        
        # Si pas de target
        if not parsed['targets']:
            return True
        
        return False
    
    def _has_correct_ports(self, parsed: Dict) -> bool:
        """Vérifie si les ports sont corrects"""
        if not self.context.get('services'):
            return True
        
        context_ports = set()
        for svc in self.context['services']:
            if svc.get('ports'):
                context_ports.update(svc['ports'])
        
        if not context_ports:
            return True
        
        # Vérifier si les ports parsés correspondent
        parsed_ports = set()
        for port_str in parsed['ports']:
            if port_str == '-':
                return True  # All ports
            
            # Parser "80,443" ou "80"
            for p in str(port_str).split(','):
                try:
                    parsed_ports.add(int(p))
                except:
                    pass
        
        # Si les ports ne correspondent pas, reconstruire
        return parsed_ports == context_ports
    
    def _rebuild_from_context(self, intentions: Dict) -> str:
        """Reconstruit complètement la commande depuis le contexte"""
        parts = ['nmap']
        
        # 1. Scan type
        if intentions['ping_scan']:
            parts.append('-sn')
        elif not intentions['ping_scan']:
            # Pas de scan type explicite, laisser nmap décider
            pass
        
        # 2. Ports (sauf si ping scan)
        if not intentions['ping_scan']:
            if intentions['all_ports']:
                parts.append('-p-')
            elif self.context.get('services'):
                ports = self._get_ports_from_context()
                if ports:
                    parts.extend(['-p', ports])
        
        # 3. Options
        if intentions['aggressive']:
            parts.append('-A')
        else:
            if self.context.get('services') and not intentions['ping_scan']:
                parts.append('-sV')
            
            if intentions['os_detect']:
                parts.append('-O')
        
        if intentions['scripts'] and not intentions['aggressive']:
            parts.append('-sC')
        
        if intentions['fast']:
            parts.append('-T4')
        
        # 4. Target
        target = self._get_target()
        if target:
            parts.append(target)
        
        return ' '.join(parts)
    
    def _fix_command(self, parsed: Dict, intentions: Dict) -> str:
        """Corrige une commande existante"""
        parts = ['nmap']
        
        # Scan type
        if parsed['scan_type']:
            parts.append(parsed['scan_type'])
        
        # Ports
        if parsed['ports'] and parsed['scan_type'] != '-sn':
            for port in parsed['ports']:
                if port == '-':
                    parts.append('-p-')
                else:
                    # Nettoyer les ports bizarres
                    clean_port = self._clean_port(port)
                    if clean_port:
                        parts.extend(['-p', clean_port])
        
        # Options
        for opt in parsed['options']:
            if opt not in parts:
                parts.append(opt)
        
        # Target
        if parsed['targets']:
            parts.append(parsed['targets'][0])
        else:
            target = self._get_target()
            if target:
                parts.append(target)
        
        return ' '.join(parts)
    
    def _clean_port(self, port_str: str) -> Optional[str]:
        """Nettoie une string de port"""
        # Enlever les caractères bizarres
        clean = re.sub(r'[^\d,\-]', '', str(port_str))
        
        # Vérifier validité
        if not clean or clean == '-':
            return None
        
        # Vérifier que ce sont des nombres valides
        for p in clean.split(','):
            if p and not p.isdigit():
                return None
            if p and (int(p) < 1 or int(p) > 65535):
                return None
        
        return clean
    
    def _get_ports_from_context(self) -> str:
        """Extrait les ports du contexte"""
        ports = []
        
        for svc in self.context.get('services', []):
            if svc.get('ports'):
                ports.extend(svc['ports'])
        
        if ports:
            unique = sorted(set(ports))
            return ','.join(map(str, unique))
        
        return ''
    
    def _get_target(self) -> str:
        """Extrait la target du contexte"""
        if self.context.get('targets'):
            return self.context['targets'][0]
        return '192.168.1.1'


# Test
if __name__ == "__main__":
    print("🧪 Tests du Post-Processor Avancé\n")
    
    # Test 1: Conflit -sn + ports
    context = {
        'services': [{'service': 'HTTP', 'ports': [80]}, {'service': 'HTTPS', 'ports': [443]}],
        'targets': ['192.168.1.0/24']
    }
    
    processor = AdvancedNmapPostProcessor(context)
    result = processor.process("nmap -sn -sV 192.168.1.0/24 -p 80,443", "scan for web servers on 192.168.1.0/24")
    
    print(f"1. Input:  nmap -sn -sV 192.168.1.0/24 -p 80,443")
    print(f"   Output: {result}")
    print(f"   Expected: nmap -p 80,443 -sV 192.168.1.0/24\n")
    
    # Test 2: Port bizarre
    context = {
        'services': [{'service': 'SSH', 'ports': [22]}],
        'targets': ['10.0.0.1']
    }
    
    processor = AdvancedNmapPostProcessor(context)
    result = processor.process("nmap -p 5310 -sV 10.0.0.1 22", "scan for SSH on 10.0.0.1")
    
    print(f"2. Input:  nmap -p 5310 -sV 10.0.0.1 22")
    print(f"   Output: {result}")
    print(f"   Expected: nmap -p 22 -sV 10.0.0.1\n")
    
    # Test 3: DNS, SNMP, Telnet
    context = {
        'services': [
            {'service': 'DNS', 'ports': [53]},
            {'service': 'SNMP', 'ports': [161]},
            {'service': 'Telnet', 'ports': [23]}
        ],
        'targets': ['172.16.0.254']
    }
    
    processor = AdvancedNmapPostProcessor(context)
    result = processor.process("nmap -p 53", "scan for DNS, SNMP and Telnet on 172.16.0.254")
    
    print(f"3. Input:  nmap -p 53")
    print(f"   Output: {result}")
    print(f"   Expected: nmap -p 23,53,161 -sV 172.16.0.254\n")
    
    print("✅ Tests terminés !")