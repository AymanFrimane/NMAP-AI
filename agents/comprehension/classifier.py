"""
Comprehension Agent - Classifier Module
Handles relevance detection and complexity classification for nmap queries.
"""

import json
import re
from pathlib import Path
from typing import Literal, Tuple, Dict, List
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


class NmapQueryClassifier:
    """Classifier for nmap query relevance and complexity detection."""
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        self.vectorizer = None
        self.complexity_model = None
        self.relevance_threshold = 0.25
        
        # Nmap-specific keywords for relevance checking
        self.nmap_keywords = {
            'scan', 'port', 'host', 'network', 'ping', 'tcp', 'udp', 'syn',
            'version', 'os', 'detection', 'script', 'traceroute', 'firewall',
            'stealth', 'service', 'vulnerability', 'nmap', 'enumerate',
            'discover', 'probe', 'fingerprint', 'timing', 'aggressive',
            'ssh', 'http', 'https', 'ftp', 'smtp', 'dns', 'snmp', 'rdp',
            'mysql', 'telnet', 'subnet', 'range', 'target', 'banner'
        }
        
    def _extract_complexity_features(self, command: str) -> Dict[str, int]:
        """Extract features from nmap command to determine complexity."""
        features = {
            'num_flags': len(re.findall(r'-[a-zA-Z0-9]+', command)),
            'has_scripts': int('--script' in command),
            'has_timing': int(bool(re.search(r'-T[0-5]', command))),
            'has_port_spec': int('-p' in command and '-p-' not in command),
            'has_all_ports': int('-p-' in command),
            'has_os_detect': int('-O' in command),
            'has_version_detect': int('-sV' in command),
            'has_udp': int('-sU' in command),
            'has_traceroute': int('--traceroute' in command),
            'has_ipv6': int('-6' in command),
            'is_ping_scan': int('-sn' in command),
            'num_port_specs': len(re.findall(r'-p\s+\d+', command)),
        }
        return features
    
    def _classify_complexity_rule_based(self, command: str) -> Literal["EASY", "MEDIUM", "HARD"]:
        """Rule-based complexity classification (fallback)."""
        features = self._extract_complexity_features(command)
        
        # HARD conditions
        if (features['has_scripts'] and features['has_udp']) or \
           (features['has_timing'] and features['has_scripts']) or \
           (features['num_flags'] > 5) or \
           (features['has_ipv6'] and features['has_version_detect']):
            return "HARD"
        
        # EASY conditions
        if (features['is_ping_scan'] and features['num_flags'] <= 2) or \
           (features['num_flags'] <= 2 and not features['has_scripts']):
            return "EASY"
        
        # Default to MEDIUM
        return "MEDIUM"
    
    def build_vocab_and_train(self, dataset_path: str) -> Tuple[float, Dict]:
        """
        Build TF-IDF vocabulary and train complexity classifier.
        
        Args:
            dataset_path: Path to nmap dataset JSON
            
        Returns:
            Tuple of (accuracy, classification_report)
        """
        # Load dataset
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        # Extract texts and labels
        texts = [item['input'] for item in data]
        commands = [item['output'] for item in data]
        
        # Create complexity labels using rule-based classification
        labels = [self._classify_complexity_rule_based(cmd) for cmd in commands]
        
        # Build TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=2,
            stop_words='english',
            lowercase=True
        )
        
        X = self.vectorizer.fit_transform(texts)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Train complexity classifier
        self.complexity_model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )
        self.complexity_model.fit(X_train, y_train)
        
        # Evaluate
        accuracy = self.complexity_model.score(X_test, y_test)
        
        # Save models
        joblib.dump(self.vectorizer, self.artifacts_dir / 'tfidf.pkl')
        joblib.dump(self.complexity_model, self.artifacts_dir / 'complexity_model.pkl')
        
        # Print distribution
        from collections import Counter
        train_dist = Counter(y_train)
        test_dist = Counter(y_test)
        
        report = {
            'accuracy': accuracy,
            'train_distribution': dict(train_dist),
            'test_distribution': dict(test_dist),
            'vocabulary_size': len(self.vectorizer.vocabulary_)
        }
        
        print(f"Training completed!")
        print(f"Accuracy: {accuracy:.3f}")
        print(f"Train distribution: {train_dist}")
        print(f"Test distribution: {test_dist}")
        
        return accuracy, report
    
    def load_models(self):
        """Load pre-trained models from artifacts."""
        vectorizer_path = self.artifacts_dir / 'tfidf.pkl'
        model_path = self.artifacts_dir / 'complexity_model.pkl'
        
        if not vectorizer_path.exists() or not model_path.exists():
            raise FileNotFoundError(
                "Models not found. Please run build_vocab_and_train() first."
            )
        
        self.vectorizer = joblib.load(vectorizer_path)
        self.complexity_model = joblib.load(model_path)
    
    def is_relevant(self, query: str) -> bool:
        """
        Check if query is relevant to nmap/network scanning.
        
        Args:
            query: User's natural language query
            
        Returns:
            True if relevant, False otherwise
        """
        if not self.vectorizer:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        query_lower = query.lower()
        
        # Quick keyword check
        has_keywords = any(kw in query_lower for kw in self.nmap_keywords)
        if not has_keywords:
            # Check TF-IDF similarity
            query_vec = self.vectorizer.transform([query])
            # Get average similarity to nmap vocabulary
            vocab_importance = np.mean(query_vec.toarray())
            return vocab_importance >= self.relevance_threshold
        
        return True
    
    def predict_complexity(self, query: str) -> Literal["EASY", "MEDIUM", "HARD"]:
        """
        Predict complexity level of the query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Complexity level: EASY, MEDIUM, or HARD
        """
        if not self.vectorizer or not self.complexity_model:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        query_vec = self.vectorizer.transform([query])
        prediction = self.complexity_model.predict(query_vec)[0]
        
        return prediction
    
    def comprehend(self, query: str) -> Dict:
        """
        Complete comprehension: relevance + complexity + intent extraction.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dict with intent, is_relevant, and complexity
        """
        is_relevant = self.is_relevant(query)
        
        if not is_relevant:
            return {
                "intent": query.strip().lower(),  # Fixed: lowercase for consistency
                "is_relevant": False,
                "complexity": None
            }
        
        complexity = self.predict_complexity(query)
        
        # Extract intent (simplified - just clean the query)
        intent = query.strip().lower()
        
        return {
            "intent": intent,
            "is_relevant": True,
            "complexity": complexity
        }


# Singleton instance
_classifier = None

def get_classifier() -> NmapQueryClassifier:
    """Get or create the classifier singleton."""
    global _classifier
    if _classifier is None:
        _classifier = NmapQueryClassifier()
        try:
            _classifier.load_models()
        except FileNotFoundError:
            print("Warning: Models not found. Please train first.")
    return _classifier