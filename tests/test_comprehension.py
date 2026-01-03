"""
Tests for Comprehension Agent
Tests relevance detection, complexity classification, and KG utilities.
"""

import pytest
import sys
import json
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.comprehension.classifier import NmapQueryClassifier
from agents.comprehension.kg_utils import Neo4jClient, NmapOption


class TestClassifier:
    """Tests for NmapQueryClassifier."""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        """Create classifier with temporary artifacts directory."""
        classifier = NmapQueryClassifier(artifacts_dir=str(tmp_path))
        
        # Create minimal training data
        train_data = [
            {"input": "Scan 192.168.1.1", "output": "nmap 192.168.1.1"},
            {"input": "Ping scan network", "output": "nmap -sn 192.168.1.0/24"},
            {"input": "Fast port scan", "output": "nmap -F 192.168.1.1"},
            {"input": "TCP SYN scan with version detection", "output": "nmap -sS -sV 192.168.1.1"},
            {"input": "Scan for HTTP and HTTPS", "output": "nmap -p 80,443 192.168.1.1"},
            {"input": "Full scan with scripts", "output": "nmap -p- -sS -sV --script vuln 192.168.1.1"},
            {"input": "UDP scan with timing", "output": "nmap -sU -T4 192.168.1.1"},
            {"input": "OS detection IPv6", "output": "nmap -O -6 ::1"},
            {"input": "Aggressive scan with evasion", "output": "nmap -A -T5 -D RND:10 192.168.1.1"},
            {"input": "Scan web servers on network", "output": "nmap -p 80,443,8080 192.168.1.0/24"},
        ]
        
        # Duplicate to create more training data
        train_data = train_data * 20  # 200 samples
        
        train_file = tmp_path / "train.json"
        with open(train_file, 'w') as f:
            json.dump(train_data, f)
        
        # Train the classifier
        classifier.build_vocab_and_train(str(train_file))
        
        return classifier
    
    def test_relevance_nmap_query(self, classifier):
        """Test that nmap-related queries are marked as relevant."""
        assert classifier.is_relevant("Scan 192.168.1.1 for open ports")
        assert classifier.is_relevant("Perform a TCP SYN scan")
        assert classifier.is_relevant("Check what services are running")
        assert classifier.is_relevant("Ping scan the network")
        assert classifier.is_relevant("Find HTTP servers")
    
    def test_irrelevance_non_nmap_query(self, classifier):
        """Test that non-nmap queries are marked as irrelevant."""
        assert not classifier.is_relevant("What is love?")
        assert not classifier.is_relevant("How to bake a cake?")
        assert not classifier.is_relevant("Tell me a joke")
        assert not classifier.is_relevant("The weather is nice today")
    
    def test_complexity_easy(self, classifier):
        """Test EASY complexity classification."""
        complexity = classifier.predict_complexity("Ping scan 192.168.1.1")
        assert complexity == "EASY"
        
        complexity = classifier.predict_complexity("Simple scan")
        assert complexity == "EASY"
    
    def test_complexity_medium(self, classifier):
        """Test MEDIUM complexity classification."""
        complexity = classifier.predict_complexity("Scan ports 80 and 443 with version detection")
        assert complexity in ["EASY", "MEDIUM"]  # Could be either
    
    def test_complexity_hard(self, classifier):
        """Test HARD complexity classification."""
        complexity = classifier.predict_complexity(
            "Full port scan with OS detection, version detection, and vulnerability scripts"
        )
        assert complexity in ["MEDIUM", "HARD"]
    
    def test_comprehend_relevant(self, classifier):
        """Test full comprehension of relevant query."""
        result = classifier.comprehend("Scan 192.168.1.0/24 for web servers")
        
        assert result["is_relevant"] is True
        assert result["intent"] == "scan 192.168.1.0/24 for web servers"
        assert result["complexity"] in ["EASY", "MEDIUM", "HARD"]
    
    def test_comprehend_irrelevant(self, classifier):
        """Test full comprehension of irrelevant query."""
        result = classifier.comprehend("What is the capital of France?")
        
        assert result["is_relevant"] is False
        assert result["intent"] == "what is the capital of france?"
        assert result["complexity"] is None
    
    def test_model_persistence(self, classifier, tmp_path):
        """Test that models can be saved and loaded."""
        # Models should already be saved from training
        vectorizer_path = tmp_path / 'tfidf.pkl'
        model_path = tmp_path / 'complexity_model.pkl'
        
        assert vectorizer_path.exists()
        assert model_path.exists()
        
        # Create new classifier and load models
        new_classifier = NmapQueryClassifier(artifacts_dir=str(tmp_path))
        new_classifier.load_models()
        
        # Test loaded classifier works
        assert new_classifier.is_relevant("Scan network")
        result = new_classifier.predict_complexity("Port scan")
        assert result in ["EASY", "MEDIUM", "HARD"]


class TestKnowledgeGraph:
    """Tests for Knowledge Graph utilities."""
    
    @pytest.fixture
    def kg_client(self):
        """Create KG client (will use fallback if Neo4j unavailable)."""
        return Neo4jClient()
    
    def test_get_all_options(self, kg_client):
        """Test retrieving all options."""
        options = kg_client.get_options()
        assert len(options) > 0
        assert all(isinstance(opt, NmapOption) for opt in options)
    
    def test_get_options_no_root(self, kg_client):
        """Test filtering options that don't require root."""
        options = kg_client.get_options(requires_root=False)
        assert len(options) > 0
        assert all(not opt.requires_root for opt in options)
        
        # Should include -sT (TCP connect) but not -sS (SYN)
        option_names = [opt.name for opt in options]
        assert "-sT" in option_names
        assert "-sS" not in option_names
    
    def test_get_options_root_required(self, kg_client):
        """Test filtering options that require root."""
        options = kg_client.get_options(requires_root=True)
        assert len(options) > 0
        assert all(opt.requires_root for opt in options)
        
        # Should include -sS (SYN) and -O (OS detection)
        option_names = [opt.name for opt in options]
        assert "-sS" in option_names
        assert "-O" in option_names
    
    def test_get_options_by_category(self, kg_client):
        """Test filtering by category."""
        scan_options = kg_client.get_options(category="SCAN_TYPE")
        assert len(scan_options) > 0
        assert all(opt.category == "SCAN_TYPE" for opt in scan_options)
        
        timing_options = kg_client.get_options(category="TIMING")
        assert len(timing_options) > 0
    
    def test_get_conflicts(self, kg_client):
        """Test retrieving conflicts for an option."""
        conflicts = kg_client.get_conflicts("-sS")
        
        # -sS should conflict with -sT, -sU, -sn
        assert "-sT" in conflicts
        assert "-sU" in conflicts
        assert "-sn" in conflicts
    
    def test_validate_command_conflicts_none(self, kg_client):
        """Test validation with no conflicts."""
        flags = ["-sS", "-p", "80,443", "-sV"]
        conflicts = kg_client.validate_command_conflicts(flags)
        
        assert len(conflicts) == 0
    
    def test_validate_command_conflicts_found(self, kg_client):
        """Test validation with conflicts."""
        # -sS and -sT are mutually exclusive
        flags = ["-sS", "-sT", "-p", "80"]
        conflicts = kg_client.validate_command_conflicts(flags)
        
        assert len(conflicts) > 0
        assert "-sS" in conflicts
        assert "-sT" in conflicts
    
    def test_exclude_conflicts(self, kg_client):
        """Test excluding conflicting options."""
        # Get scan types that don't conflict with -sS
        options = kg_client.get_options(
            category="SCAN_TYPE",
            exclude_conflicts=["-sS"]
        )
        
        option_names = [opt.name for opt in options]
        
        # Should include -sS itself
        assert "-sS" in option_names
        
        # Should NOT include -sT (conflicts with -sS)
        assert "-sT" not in option_names


class TestIntegration:
    """Integration tests combining classifier and KG."""
    
    @pytest.fixture
    def classifier(self, tmp_path):
        """Create trained classifier."""
        classifier = NmapQueryClassifier(artifacts_dir=str(tmp_path))
        
        # Use actual dataset if available
        dataset_path = Path(__file__).parent.parent.parent / "nmap_dataset.json"
        
        if dataset_path.exists():
            classifier.build_vocab_and_train(str(dataset_path))
        else:
            # Create minimal dataset
            train_data = [
                {"input": "Scan network", "output": "nmap 192.168.1.0/24"},
                {"input": "Port scan", "output": "nmap -p- 192.168.1.1"},
            ] * 50
            
            train_file = tmp_path / "train.json"
            with open(train_file, 'w') as f:
                json.dump(train_data, f)
            classifier.build_vocab_and_train(str(train_file))
        
        return classifier
    
    @pytest.fixture
    def kg_client(self):
        """Create KG client."""
        return Neo4jClient()
    
    def test_workflow_easy_query(self, classifier, kg_client):
        """Test complete workflow for EASY query."""
        query = "Ping scan 192.168.1.0/24"
        
        # Step 1: Comprehend
        result = classifier.comprehend(query)
        assert result["is_relevant"] is True
        
        # Step 2: Get appropriate options based on complexity
        if result["complexity"] == "EASY":
            # For EASY, we want simple options, no root required
            options = kg_client.get_options(requires_root=False)
            assert len(options) > 0
    
    def test_workflow_root_detection(self, classifier, kg_client):
        """Test workflow handles root requirement correctly."""
        query = "TCP SYN scan with OS detection"
        
        result = classifier.comprehend(query)
        
        if result["complexity"] in ["MEDIUM", "HARD"]:
            # Get root-required options
            root_options = kg_client.get_options(requires_root=True)
            option_names = [opt.name for opt in root_options]
            
            # Should include -sS and -O
            assert "-sS" in option_names
            assert "-O" in option_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])