"""
Pipeline Final NMAP-AI : T5 Premium + KG-RAG
Architecture professionnelle avec post-processing intelligent
"""

import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / 'agents' / 'easy_medium'))

from knowledge_graph_rag import NmapKnowledgeGraphRAG
from t5_generator import T5NmapGenerator
from advanced_postprocessor import AdvancedNmapPostProcessor


class FinalNmapPipeline:
    """Pipeline final T5 Premium + KG-RAG"""
    
    def __init__(
        self,
        kg_uri: str = "bolt://localhost:7687",
        kg_user: str = "neo4j",
        kg_password: str = "nmap1234"
    ):
        print("🚀 Initialisation du Pipeline Final NMAP-AI...")
        
        # Knowledge Graph RAG
        print("📊 Connexion au Knowledge Graph...")
        self.kg_rag = NmapKnowledgeGraphRAG(kg_uri, kg_user, kg_password)
        
        # T5 Generator (Premium) - Chemin complet
        print("🤖 Chargement de T5 Premium...")
        adapter_path = Path(__file__).parent.parent / 'agents' / 'easy_medium' / 'models' / 'nmap_adapter_premium'
        
        if not adapter_path.exists():
            # Fallback: essayer depuis le dossier courant
            adapter_path = "nmap_adapter_premium"
        
        print(f"   Adapter path: {adapter_path}")
        self.t5_gen = T5NmapGenerator(adapter_path=str(adapter_path))
        
        print("✅ Pipeline Final initialisé avec succès !")
    
    def generate(self, query: str, use_rag: bool = True) -> Dict:
        """
        Génère une commande nmap
        
        Args:
            query: Requête en langage naturel
            use_rag: Utiliser le RAG pour enrichir
        
        Returns:
            Résultat complet
        """
        result = {
            'query': query,
            'enriched_query': query,
            'context': {},
            'raw_command': '',
            'final_command': '',
            'services': [],
            'explanation': ''
        }
        
        # Étape 1: Enrichir avec le RAG
        if use_rag:
            context = self.kg_rag.enrich_query(query)
            result['context'] = context
            result['services'] = [s['service'] for s in context['services']] if context['services'] else []
            
            # Enrichir la requête avec les infos du contexte
            result['enriched_query'] = self._create_enriched_query(query, context)
        
        # Étape 2: Générer avec T5
        result['raw_command'] = self.t5_gen.generate(result['enriched_query'])
        
        # Étape 3: Post-processing intelligent avancé
        postprocessor = AdvancedNmapPostProcessor(result['context'])
        result['final_command'] = postprocessor.process(result['raw_command'], query)
        
        # Étape 4: Générer explication
        result['explanation'] = self._generate_explanation(result)
        
        return result
    
    def _create_enriched_query(self, query: str, context: Dict) -> str:
        """Crée une requête enrichie pour T5"""
        
        enriched_parts = [query]
        
        # Ajouter les ports si détectés
        if context.get('services'):
            ports = []
            for service in context['services']:
                if service.get('ports'):
                    ports.extend(service['ports'])
            
            if ports:
                unique_ports = sorted(set(ports))
                ports_str = ','.join(map(str, unique_ports))
                enriched_parts.append(f"ports {ports_str}")
        
        # Ajouter les options recommandées
        if context.get('scan_type'):
            enriched_parts.append(context['scan_type'])
        
        return ' '.join(enriched_parts)
    
    def _generate_explanation(self, result: Dict) -> str:
        """Génère une explication de la commande"""
        
        parts = []
        
        if result['services']:
            parts.append(f"Services: {', '.join(result['services'])}")
        
        context = result.get('context', {})
        
        if context.get('ports'):
            ports_str = ','.join(map(str, context['ports']))
            parts.append(f"Ports: {ports_str}")
        
        if '-sV' in result['final_command']:
            parts.append("Version detection")
        
        if '-O' in result['final_command']:
            parts.append("OS detection")
        
        if '-A' in result['final_command']:
            parts.append("Aggressive scan")
        
        return ' | '.join(parts) if parts else 'Standard scan'
    
    def generate_batch(self, queries: List[str]) -> List[Dict]:
        """Génère pour plusieurs requêtes"""
        return [self.generate(q) for q in queries]
    
    def compare_with_without_rag(self, query: str):
        """Compare les résultats avec/sans RAG"""
        
        print(f"\n{'='*70}")
        print(f"🔍 Comparaison: {query}")
        print(f"{'='*70}")
        
        # Sans RAG
        result_no_rag = self.generate(query, use_rag=False)
        
        # Avec RAG
        result_with_rag = self.generate(query, use_rag=True)
        
        print(f"\n❌ SANS RAG:")
        print(f"   Commande: {result_no_rag['final_command']}")
        
        print(f"\n✅ AVEC RAG:")
        if result_with_rag['services']:
            print(f"   Services: {result_with_rag['services']}")
        print(f"   Commande: {result_with_rag['final_command']}")
        print(f"   💡 {result_with_rag['explanation']}")
        
        print(f"\n{'='*70}\n")
    
    def close(self):
        """Ferme les connexions"""
        self.kg_rag.close()
        print("👋 Pipeline fermé")


def main():
    """Démonstration"""
    
    print("\n" + "="*70)
    print("🎯 PIPELINE FINAL NMAP-AI : T5 Premium + KG-RAG")
    print("="*70)
    
    # Créer le pipeline
    pipeline = FinalNmapPipeline()
    
    # Tests
    test_queries = [
        "scan for web servers on 192.168.1.0/24",
        "scan for SSH on 10.0.0.1",
        "perform OS detection on 172.16.0.1",
        "scan all ports on 192.168.1.1",
        "do a ping scan on 10.0.0.0/24",
        "scan for DNS, SNMP and Telnet on 172.16.0.254",
        "aggressive scan with scripts on 10.0.0.1",
        "fast scan for database services on 192.168.0.0/24",
    ]
    
    print("\n📝 Tests avec RAG:\n")
    
    for i, query in enumerate(test_queries, 1):
        result = pipeline.generate(query)
        
        print(f"{i}. Query: {query}")
        
        if result['services']:
            print(f"   Services: {result['services']}")
        
        print(f"   → {result['final_command']}")
        print(f"   💡 {result['explanation']}\n")
    
    # Comparaison
    print("\n" + "="*70)
    print("🔬 COMPARAISON AVEC/SANS RAG")
    print("="*70)
    
    pipeline.compare_with_without_rag("scan for web servers on 192.168.1.0/24")
    
    # Mode interactif
    print("\n" + "="*70)
    print("💬 MODE INTERACTIF")
    print("="*70)
    print("Tapez une requête (ou 'quit' pour quitter)\n")
    
    while True:
        try:
            query = input("Requête: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            result = pipeline.generate(query)
            
            print(f"\n✅ Commande générée:")
            print(f"   {result['final_command']}")
            
            if result['explanation']:
                print(f"   💡 {result['explanation']}")
            
            if result['services']:
                print(f"   📊 Services: {result['services']}")
            
            print()
        
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}\n")
            import traceback
            traceback.print_exc()
    
    pipeline.close()


if __name__ == "__main__":
    main()