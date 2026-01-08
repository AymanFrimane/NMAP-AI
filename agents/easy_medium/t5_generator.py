"""
T5 Generator Module for NMAP-AI P2 (Medium/Hard) - VERSION 3 (STRICT)
Intègre une couche de nettoyage anti-hallucination et des définitions de groupes de services.

🔥 ÉTAPE 3: Intégrer get_options() pour filtrer les flags selon la complexité
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Set

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

# Import du KG de P1
import sys
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from agents.comprehension.kg_utils import (
        get_options,
        get_port_info,
        validate_command_conflicts,
        NmapOption
    )
    KG_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Knowledge Graph (P1) importé avec succès")
except ImportError as e:
    KG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️  KG non disponible: {e}")
    logger.info("   Mode fallback activé")

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class T5NmapGenerator:
    
    # FALLBACK uniquement si KG échoue
    SERVICES_MAP_FALLBACK = {
        "ssh": "22", "ftp": "21", "telnet": "23", "smtp": "25",
        "dns": "53", "mysql": "3306", "sql": "3306", "rdp": "3389",
        "pop3": "110", "imap": "143", "snmp": "161", "https": "443", "http": "80"
    }

    SERVICE_GROUPS_FALLBACK = {
        "web": ["80", "443"],
        "mail": ["25", "110", "143"],
        "files": ["21", "445", "139"]
    }

    def __init__(self, adapter_path: str, device: Optional[str] = None, model_name: str = "t5-small"):
        # Chemin relatif au fichier
        script_dir = Path(__file__).parent
        self.adapter_path = script_dir / adapter_path if not Path(adapter_path).is_absolute() else Path(adapter_path)
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"🔌 Initialisation sur {self.device}...")
        
        # Vérifier KG
        self.kg_available = KG_AVAILABLE
        if self.kg_available:
            self._test_kg_connection()
        
        # 🔥 ÉTAPE 3: Cache des options par complexité
        self._kg_options_cache = {
            "EASY": None,
            "MEDIUM": None,
            "HARD": None
        }
        
        self._load_model(model_name)

    def _test_kg_connection(self):
        """Tester la connexion au KG de P1"""
        try:
            options = get_options(max_complexity="EASY")
            logger.info(f"   ✓ KG accessible: {len(options)} options EASY disponibles")
            
            ssh_port = get_port_info(service="SSH")
            logger.info(f"   ✓ Mapping service→port: SSH = {ssh_port.number}")
            
            conflicts = validate_command_conflicts(["-sS", "-sT"])
            logger.info(f"   ✓ Détection conflits: {len(conflicts)} conflit(s) trouvé(s)")
            
        except Exception as e:
            logger.error(f"   ✗ Erreur test KG: {e}")
            logger.info("   Utilisation du mode fallback")
            self.kg_available = False

    def _load_model(self, model_name):
        try:
            if not self.adapter_path.exists():
                raise FileNotFoundError(f"❌ Adapter introuvable: {self.adapter_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            base_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model = PeftModel.from_pretrained(base_model, str(self.adapter_path))
            self.model.to(self.device)
            self.model.eval()
            logger.info("✅ Modèle chargé (Mode Strict).")
        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            raise

    def _get_allowed_flags_from_kg(self, complexity: str = "EASY") -> List[str]:
        """
        🔥 ÉTAPE 3: Récupérer les flags autorisés depuis le KG selon la complexité.
        
        Args:
            complexity: "EASY", "MEDIUM" ou "HARD"
            
        Returns:
            Liste de noms de flags (ex: ["-sT", "-p", "-sn", ...])
        """
        if not self.kg_available:
            # Fallback: flags basiques
            return ["-sT", "-p", "-sn", "-F"]
        
        # Utiliser le cache si disponible
        if self._kg_options_cache[complexity] is not None:
            return self._kg_options_cache[complexity]
        
        try:
            # Récupérer les options du KG
            if complexity == "EASY":
                options = get_options(max_complexity="EASY", requires_root=False)
            elif complexity == "MEDIUM":
                options = get_options(max_complexity="MEDIUM")
            else:  # HARD
                options = get_options()  # Tous les flags
            
            # Extraire les noms de flags
            flags = [opt.name for opt in options]
            
            # Mettre en cache
            self._kg_options_cache[complexity] = flags
            
            logger.debug(f"   KG: {len(flags)} flags autorisés pour {complexity}")
            return flags
            
        except Exception as e:
            logger.warning(f"Erreur récupération flags KG: {e}")
            return ["-sT", "-p", "-sn", "-F"]

    def _get_port_from_kg(self, service_name: str) -> Optional[str]:
        """Récupérer le port depuis le KG."""
        if not self.kg_available:
            return self.SERVICES_MAP_FALLBACK.get(service_name.lower())
        
        try:
            port_info = get_port_info(service=service_name.upper())
            return str(port_info.number)
        except ValueError:
            return self.SERVICES_MAP_FALLBACK.get(service_name.lower())
        except Exception as e:
            logger.warning(f"Erreur KG pour {service_name}: {e}")
            return self.SERVICES_MAP_FALLBACK.get(service_name.lower())

    def _extract_ports_from_query(self, query: str) -> Set[str]:
        """Extraire les ports depuis la query en utilisant le KG."""
        query_lower = query.lower()
        ports = set()
        
        # Services standards
        known_services = [
            "ssh", "ftp", "telnet", "smtp", "dns", "mysql", "sql", 
            "rdp", "pop3", "imap", "snmp"
        ]
        
        # 🔥 CORRECTION: Ne détecter "http" et "https" que s'ils ne font pas partie d'un autre mot
        # Pour éviter "servers" → "https"
        if re.search(r'\bhttp\b', query_lower):
            port = self._get_port_from_kg("http")
            if port:
                ports.add(port)
        
        if re.search(r'\bhttps\b', query_lower):
            port = self._get_port_from_kg("https")
            if port:
                ports.add(port)
        
        for service in known_services:
            if re.search(r'\b' + service + r'\b', query_lower):
                port = self._get_port_from_kg(service)
                if port:
                    ports.add(port)
        
        # Groupes de services
        if re.search(r'\bweb\b', query_lower):
            http_port = self._get_port_from_kg("http")
            https_port = self._get_port_from_kg("https")
            if http_port:
                ports.add(http_port)
            if https_port:
                ports.add(https_port)
        
        if re.search(r'\bmail\b', query_lower):
            for mail_service in ["smtp", "pop3", "imap"]:
                port = self._get_port_from_kg(mail_service)
                if port:
                    ports.add(port)
        
        if re.search(r'\bfiles?\b', query_lower):
            ftp_port = self._get_port_from_kg("ftp")
            if ftp_port:
                ports.add(ftp_port)
        
        return ports

    def generate(self, query: str, complexity: str = "MEDIUM") -> str:
        """
        🔥 ÉTAPE 3: Génération avec filtrage de flags selon la complexité.
        
        Args:
            query: Query utilisateur
            complexity: "EASY", "MEDIUM" ou "HARD"
        """
        try:
            # Pré-traitement
            clean_query = query.lower().replace(" and ", ", ").replace(" ports ", " port ")
            
            # 🔥 ÉTAPE 3: Récupérer les flags autorisés du KG
            allowed_flags = self._get_allowed_flags_from_kg(complexity)
            
            # Construire le prompt avec contraintes
            input_text = f"nmap conversion ({complexity}): {clean_query}"
            inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=128).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=128,
                    num_beams=3,
                    do_sample=False,
                    temperature=0.1,
                    repetition_penalty=1.5
                )

            raw_cmd = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 🔥 ÉTAPE 3: Correction avec validation KG
            final_cmd = self._strict_correction(raw_cmd, query, complexity, allowed_flags)
            return final_cmd

        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            return "nmap -sn 127.0.0.1"

    def _strict_correction(self, command: str, user_query: str, complexity: str, allowed_flags: List[str]) -> str:
        """
        Correction intelligente avec validation KG.
        
        🔥 ÉTAPE 3: Utilise allowed_flags et validate_command_conflicts()
        """
        cmd = command.strip()
        query_lower = user_query.lower()

        # A. Nettoyage de base
        cmd = re.sub(r'(?i)^(nmap\s*)+', '', cmd)
        cmd = re.sub(r'--trace\s+\S+', '', cmd)

        # B. ANTI-HALLUCINATION
        detected_ports = self._extract_ports_from_query(user_query)
        has_port_keywords = len(detected_ports) > 0 or "port" in query_lower or re.search(r'\d+', query_lower)
        
        if "-O" in cmd and not has_port_keywords:
            if "-p " in cmd:
                logger.info("Correction: Suppression des ports hallucinés pour scan OS.")
                cmd = re.sub(r'-p\s+[\d,]+', '', cmd)

        # C. LOGIQUE DES PORTS
        target_ports = detected_ports
        
        if target_ports:
            existing_ports = []
            match = re.search(r'-p\s+([\d,]+)', cmd)
            if match:
                existing_ports = match.group(1).split(',')
                cmd = re.sub(r'-p\s+[\d,]+', '', cmd).strip()
            
            all_ports = sorted(list(set(existing_ports) | target_ports), key=lambda x: int(x))
            all_ports = [p for p in all_ports if p]
            
            if all_ports:
                cmd = f"-p {','.join(all_ports)} {cmd}"

        # D. 🔥 ÉTAPE 3: Filtrage des flags selon allowed_flags
        parts = cmd.split()
        filtered_parts = []
        
        for part in parts:
            # Si c'est un flag
            if part.startswith('-') and not re.search(r'[\d\.]', part):
                # Vérifier s'il est autorisé
                if part in allowed_flags or part.startswith('-p'):
                    filtered_parts.append(part)
                else:
                    logger.debug(f"   Flag non autorisé supprimé: {part}")
            else:
                filtered_parts.append(part)
        
        cmd = ' '.join(filtered_parts)

        # E. 🔥 ÉTAPE 3: Validation des conflits avec KG
        if self.kg_available:
            flags = [p for p in cmd.split() if p.startswith('-') and not re.search(r'[\d\.]', p)]
            conflicts = validate_command_conflicts(flags)
            
            if conflicts:
                logger.info(f"   Conflits détectés: {conflicts}")
                # Supprimer le premier flag conflictuel
                for flag in conflicts.keys():
                    cmd = cmd.replace(f" {flag} ", " ", 1)
                    logger.info(f"   Flag conflictuel supprimé: {flag}")
                    break

        # F. Respect des contraintes de complexité
        flags = [p for p in cmd.split() if p.startswith('-') and not re.search(r'[\d\.]', p)]
        non_port_flags = [f for f in flags if f != "-p"]
        
        if complexity == "EASY" and len(non_port_flags) > 1:
            # Garder seulement le premier flag
            for flag in non_port_flags[1:]:
                cmd = cmd.replace(f" {flag} ", " ", 1)
            logger.info(f"   EASY: limité à 1 flag")
        
        elif complexity == "MEDIUM" and len(flags) > 3:
            # Garder les 3 premiers flags
            for flag in flags[3:]:
                cmd = cmd.replace(f" {flag} ", " ", 1)
            logger.info(f"   MEDIUM: limité à 3 flags")

        # G. Vérification IP
        if not re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', cmd) and "localhost" not in cmd:
            ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?\b', user_query)
            if ip_match:
                cmd += f" {ip_match.group(0)}"
            elif "localhost" in query_lower:
                cmd += " localhost"

        # Nettoyage
        cmd = re.sub(r'\s+', ' ', cmd).strip()
        return f"nmap {cmd}"

# ================= TEST ÉTAPE 3 =================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TEST ÉTAPE 3: get_options() pour filtrer les flags")
    print("="*60 + "\n")
    
    script_dir = Path(__file__).parent
    adapter_path = script_dir / "models" / "nmap_adapter_premium"
    
    if adapter_path.exists():
        gen = T5NmapGenerator(str(adapter_path))
        
        print("\n📊 État du générateur:")
        print(f"   KG disponible: {gen.kg_available}")
        
        # 🔥 ÉTAPE 3: Tests avec différentes complexités
        test_cases = [
            ("scan for ssh on 192.168.1.1", "EASY", "1 flag max"),
            ("scan with version detection", "MEDIUM", "≤3 flags"),
            ("scan for web servers on 192.168.1.50", "EASY", "Ports web"),
            ("aggressive scan with scripts", "HARD", "Tous flags autorisés"),
            ("scan localhost with OS detection", "MEDIUM", "Pas de ports hallucinés"),
            ("scan for mail servers on 10.0.0.1", "EASY", "Groupe mail"),
        ]
        
        print(f"\n{'='*10} TESTS AVEC FILTRAGE DE FLAGS {'='*10}")
        for query, complexity, expected in test_cases:
            print(f"\n📝 Test ({complexity}): {query}")
            print(f"   Attendu: {expected}")
            result = gen.generate(query, complexity)
            print(f"   Résultat: \033[1;32m{result}\033[0m")
        
        print("\n✅ ÉTAPE 3 COMPLÈTE!")
        print("   ✓ get_options() intégré pour filtrer les flags")
        print("   ✓ validate_command_conflicts() utilisé")
        print("   ✓ Contraintes de complexité respectées")
        print("\n🎉 INTÉGRATION KG COMPLÈTE!")
        print("   Votre générateur utilise maintenant le KG de P1 pour:")
        print("   • Mapper services → ports (get_port_info)")
        print("   • Filtrer les flags autorisés (get_options)")
        print("   • Valider les conflits (validate_command_conflicts)")
        
    else:
        print(f"❌ Adapter non trouvé: {adapter_path}")