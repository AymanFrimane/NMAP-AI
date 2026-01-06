"""
T5 Generator Module for NMAP-AI P2 (Easy/Medium)

Ce module charge l'adapter T5 fine-tuné et génère des commandes nmap
à partir de requêtes en langage naturel.

Auteur: NMAP-AI Team
Date: 2025
"""

import re
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
from peft import PeftModel, PeftConfig

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class T5NmapGenerator:
    """
    Générateur de commandes nmap basé sur T5 + LoRA
    
    Utilise un modèle T5-small fine-tuné avec LoRA pour convertir
    des requêtes en langage naturel en commandes nmap valides.
    """
    
    def __init__(
        self,
        adapter_path: str,
        device: Optional[str] = None,
        max_length: int = 64,
        num_beams: int = 5
    ):
        """
        Initialise le générateur T5
        
        Args:
            adapter_path: Chemin vers l'adapter LoRA
            device: Device PyTorch ('cuda', 'cpu', ou None pour auto)
            max_length: Longueur maximale de génération
            num_beams: Nombre de beams pour beam search
        """
        self.adapter_path = Path(adapter_path)
        self.max_length = max_length
        self.num_beams = num_beams
        
        # Déterminer le device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initialisation du générateur T5 sur {self.device}")
        
        # Charger le modèle et le tokenizer
        self._load_model()
        
        logger.info("✅ Générateur T5 initialisé avec succès")
    
    def _load_model(self):
        """Charge le modèle T5 et l'adapter LoRA"""
        try:
            # Vérifier que l'adapter existe
            if not self.adapter_path.exists():
                raise FileNotFoundError(
                    f"Adapter non trouvé : {self.adapter_path}\n"
                    f"Assurez-vous d'avoir téléchargé l'adapter depuis Colab."
                )
            
            logger.info(f"Chargement de l'adapter depuis {self.adapter_path}")
            
            # Charger la config LoRA
            config = PeftConfig.from_pretrained(str(self.adapter_path))
            
            # Charger le modèle de base T5
            logger.info(f"Chargement du modèle de base : {config.base_model_name_or_path}")
            base_model = T5ForConditionalGeneration.from_pretrained(
                config.base_model_name_or_path
            )
            
            # Charger l'adapter LoRA
            self.model = PeftModel.from_pretrained(base_model, str(self.adapter_path))
            self.model.to(self.device)
            self.model.eval()
            
            # Charger le tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(str(self.adapter_path))
            
            logger.info("✅ Modèle et adapter chargés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement du modèle : {e}")
            raise
    
    def generate(
        self,
        query: str,
        temperature: float = 1.0,
        do_sample: bool = False,
        **kwargs
    ) -> str:
        """
        Génère une commande nmap à partir d'une requête
        
        Args:
            query: Requête en langage naturel
            temperature: Température de génération (1.0 = déterministe)
            do_sample: Utiliser sampling ou beam search
            **kwargs: Arguments supplémentaires pour generate()
        
        Returns:
            Commande nmap générée et post-traitée
            
        Example:
            >>> generator = T5NmapGenerator("models/nmap_adapter_premium")
            >>> cmd = generator.generate("scan for web servers on 192.168.1.0/24")
            >>> print(cmd)
            "nmap -p 80,443 -sV 192.168.1.0/24"
        """
        try:
            # Préparer l'input avec le préfixe T5
            input_text = f"translate English to Nmap command: {query}"
            
            # Tokenizer
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=128,
                truncation=True
            ).to(self.device)
            
            # Générer
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    num_beams=self.num_beams,
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                    repetition_penalty=1.3,
                    length_penalty=1.0,
                    temperature=temperature,
                    do_sample=do_sample,
                    **kwargs
                )
            
            # Décoder
            command = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Post-processing
            command = self._post_process(command, query)
            
            return command
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération : {e}")
            raise
    
    def _post_process(self, command: str, query: str) -> str:
        """
        Post-traitement pour nettoyer et valider la commande
        
        Args:
            command: Commande brute générée
            query: Requête originale (pour extraire IPs si besoin)
        
        Returns:
            Commande nettoyée et validée
        """
        # Nettoyer les espaces
        command = re.sub(r'\s+', ' ', command).strip()
        
        # Supprimer les commentaires après ':'
        if ':' in command:
            command = command.split(':')[0].strip()
        
        # Assurer que commence par 'nmap '
        if not command.startswith('nmap '):
            if command.startswith('nmap'):
                command = 'nmap ' + command[4:].lstrip()
            else:
                command = 'nmap ' + command
        
        # Nettoyer les tokens
        tokens = command.split()
        cleaned = ['nmap']
        seen_flags = set()
        
        i = 1
        while i < len(tokens):
            token = tokens[i]
            
            # Flags
            if token.startswith('-'):
                # Valider le flag avec regex
                if re.match(r'^--?[a-zA-Z0-9]+$', token):
                    # Flag avec valeur (ex: -p 80)
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                        pair = f"{token}:{tokens[i + 1]}"
                        if pair not in seen_flags:
                            cleaned.append(token)
                            cleaned.append(tokens[i + 1])
                            seen_flags.add(pair)
                        i += 2
                        continue
                    # Flag simple
                    else:
                        if token not in seen_flags:
                            cleaned.append(token)
                            seen_flags.add(token)
            # Cibles (IPs, domaines)
            else:
                cleaned.append(token)
            
            i += 1
        
        # Vérifier si une cible est présente
        has_target = any(not t.startswith('-') for t in cleaned[1:])
        
        # Si pas de cible, essayer d'en extraire une de la query
        if not has_target:
            # Chercher une IP dans la query
            ip_match = re.search(
                r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?\b',
                query
            )
            if ip_match:
                cleaned.append(ip_match.group())
            else:
                # Placeholder par défaut
                cleaned.append('192.168.1.1')
        
        return ' '.join(cleaned)
    
    def batch_generate(self, queries: list[str], **kwargs) -> list[str]:
        """
        Génère des commandes pour plusieurs requêtes
        
        Args:
            queries: Liste de requêtes en langage naturel
            **kwargs: Arguments pour generate()
        
        Returns:
            Liste de commandes nmap
        """
        return [self.generate(query, **kwargs) for query in queries]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le modèle
        
        Returns:
            Dictionnaire avec les infos du modèle
        """
        return {
            'adapter_path': str(self.adapter_path),
            'device': self.device,
            'base_model': self.model.config._name_or_path,
            'max_length': self.max_length,
            'num_beams': self.num_beams,
            'trainable_params': sum(
                p.numel() for p in self.model.parameters() if p.requires_grad
            ),
            'total_params': sum(p.numel() for p in self.model.parameters())
        }


# Fonction helper pour usage simple
def generate_nmap_command(
    query: str,
    adapter_path: str = "models/nmap_adapter_premium"
) -> str:
    """
    Fonction helper pour génération rapide
    
    Args:
        query: Requête en langage naturel
        adapter_path: Chemin vers l'adapter
    
    Returns:
        Commande nmap générée
        
    Example:
        >>> from t5_generator import generate_nmap_command
        >>> cmd = generate_nmap_command("scan for SSH on 192.168.1.0/24")
        >>> print(cmd)
    """
    generator = T5NmapGenerator(adapter_path)
    return generator.generate(query)


if __name__ == "__main__":
    """
    Test du générateur en mode standalone
    """
    import sys
    
    # Chemin de l'adapter (ajuster si nécessaire)
    ADAPTER_PATH = "models/nmap_adapter_premium"
    
    # Vérifier que l'adapter existe
    if not Path(ADAPTER_PATH).exists():
        print(f"❌ Adapter non trouvé : {ADAPTER_PATH}")
        print("Assurez-vous d'avoir téléchargé l'adapter depuis Colab.")
        sys.exit(1)
    
    # Créer le générateur
    print("🚀 Initialisation du générateur T5...")
    generator = T5NmapGenerator(ADAPTER_PATH)
    
    # Afficher les infos
    print("\n📊 Informations du modèle:")
    info = generator.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Tests
    print("\n🧪 Tests de génération:\n")
    
    test_queries = [
        "scan all ports on 192.168.1.1",
        "do a ping scan on 10.0.0.0/24",
        "scan for web servers on 192.168.0.1",
        "perform OS detection on 172.16.0.1",
        "scan for SSH with version detection",
    ]
    
    for i, query in enumerate(test_queries, 1):
        command = generator.generate(query)
        print(f"{i}. Query: {query}")
        print(f"   Command: {command}\n")
    
    # Mode interactif
    print("\n💬 Mode interactif (tapez 'quit' pour quitter):\n")
    
    while True:
        try:
            query = input("Requête: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if not query:
                continue
            
            command = generator.generate(query)
            print(f"→ {command}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}\n")