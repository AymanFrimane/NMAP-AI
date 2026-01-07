"""
Hard Generator - T5-based Nmap Command Generator
Place this in: agents/hard/t5_generator.py
"""

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from peft import PeftModel
import os
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class HardGenerator:
    """
    Generates complex Nmap commands using fine-tuned T5-base + LoRA
    
    Handles:
    - Advanced Nmap scripts (vuln, brute-force, etc.)
    - Timing and evasion techniques
    - IPv6 support
    - Output format specifications
    - UDP scans with automatic sudo handling
    """
    
    def __init__(
        self,
        adapter_path: str = "./agents/hard/adapter",
        base_model: str = "t5-base",
        device: Optional[str] = None
    ):
        """
        Initialize the hard generator
        
        Args:
            adapter_path: Path to LoRA adapter directory
            base_model: Base model name (default: t5-base)
            device: Device to use (cuda/cpu, auto-detected if None)
        """
        self.adapter_path = adapter_path
        self.base_model = base_model
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.model = None
        self.tokenizer = None
        self.max_length = 256
        
        logger.info(f"Initialized HardGenerator (device: {self.device})")
    
    def load_adapter(self) -> None:
        """Load the base model and LoRA adapter"""
        logger.info(f"Loading adapter from {self.adapter_path}...")
        
        try:
            # Load tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(self.adapter_path)
            
            # Load base model
            base_model = T5ForConditionalGeneration.from_pretrained(
                self.base_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(base_model, self.adapter_path)
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"✅ Hard generator loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load adapter: {e}")
            raise
    
    def generate(
        self,
        intent: str,
        kg_hints: Optional[Dict[str, Any]] = None,
        max_new_tokens: int = 100,
        num_beams: int = 4
    ) -> str:
        """
        Generate a complex Nmap command from natural language intent
        
        Args:
            intent: Natural language description of the scan
            kg_hints: Optional hints from Knowledge Graph (e.g., required flags, conflicts)
            max_new_tokens: Maximum tokens to generate
            num_beams: Number of beams for beam search
            
        Returns:
            Generated Nmap command string
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_adapter() first.")
        
        # Format input for T5
        input_text = f"generate nmap command: {intent}"
        
        # Add KG hints if provided
        if kg_hints and 'allowed_flags' in kg_hints and kg_hints['allowed_flags']:
            flags = ', '.join(kg_hints['allowed_flags'][:5])  # Limit to 5
            input_text += f" (flags: {flags})"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_length,
                num_beams=num_beams,
                early_stopping=True,
                do_sample=False  # Deterministic generation
            )
        
        # Decode
        command = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean and post-process
        command = self._clean_command(command, intent)
        
        # Auto-add sudo if needed
        if self._requires_sudo(command):
            command = f"sudo {command}"
        
        return command.strip()
    
    def _clean_command(self, cmd: str, intent: str) -> str:
        """
        Clean and fix common generation errors
        
        Args:
            cmd: Generated command
            intent: Original intent
            
        Returns:
            Cleaned command
        """
        # Remove literal words that shouldn't be in commands
        bad_words = ['XML', 'output', 'common', 'ports', 'servers']
        for word in bad_words:
            if f' {word} ' in cmd or f' {word}' in cmd:
                cmd = cmd.replace(f' {word}', '')
        
        # Remove duplicate flags
        parts = cmd.split()
        seen_flags = set()
        cleaned = []
        
        for part in parts:
            if part.startswith('-'):
                if part not in seen_flags:
                    cleaned.append(part)
                    seen_flags.add(part)
            else:
                cleaned.append(part)
        
        cmd = ' '.join(cleaned)
        
        # Add missing critical flags based on intent
        intent_lower = intent.lower()
        
        # UDP scans
        if 'udp' in intent_lower and '-sU' not in cmd:
            cmd = cmd.replace('nmap', 'nmap -sU', 1)
        
        # XML output
        if 'xml' in intent_lower and '-oX' not in cmd:
            cmd += ' -oX output.xml'
        
        # Scripts
        if 'brute' in intent_lower and '--script' not in cmd:
            if 'snmp' in intent_lower:
                cmd = cmd.replace('nmap', 'nmap --script snmp-brute', 1)
            elif 'ftp' in intent_lower:
                cmd = cmd.replace('nmap', 'nmap --script ftp-brute', 1)
        
        if 'vuln' in intent_lower and '--script' not in cmd:
            cmd = cmd.replace('nmap', 'nmap --script vuln', 1)
        
        return cmd.strip()
    
    def _requires_sudo(self, command: str) -> bool:
        """
        Check if command requires sudo (e.g., UDP scans, raw packets)
        
        Args:
            command: The nmap command
            
        Returns:
            True if sudo should be added
        """
        # Don't add sudo if already present
        if command.startswith('sudo'):
            return False
        
        # Flags that require root privileges
        root_flags = [
            '-sU',  # UDP scan
            '-sN',  # TCP Null scan
            '-sF',  # FIN scan
            '-sX',  # Xmas scan
            '-sA',  # ACK scan
            '-sW',  # Window scan
            '-sM',  # Maimon scan
            '--scanflags',  # Custom TCP scan
            '-O',   # OS detection (usually requires root)
        ]
        
        return any(flag in command for flag in root_flags)
    
    def batch_generate(
        self,
        intents: List[str],
        kg_hints_list: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate commands for multiple intents
        
        Args:
            intents: List of natural language intents
            kg_hints_list: Optional list of KG hints (one per intent)
            **kwargs: Additional arguments for generate()
            
        Returns:
            List of generated commands
        """
        if kg_hints_list is None:
            kg_hints_list = [None] * len(intents)
        
        commands = []
        for intent, hints in zip(intents, kg_hints_list):
            try:
                cmd = self.generate(intent, kg_hints=hints, **kwargs)
                commands.append(cmd)
            except Exception as e:
                logger.error(f"Failed to generate for '{intent}': {e}")
                commands.append(f"nmap {intent}")  # Fallback
        
        return commands


# Convenience function for quick usage
def generate_hard(
    intent: str,
    kg_hints: Optional[Dict[str, Any]] = None,
    adapter_path: str = "./agents/hard/adapter"
) -> str:
    """
    Quick function to generate a hard command without managing the generator object
    
    Args:
        intent: Natural language description
        kg_hints: Optional KG hints
        adapter_path: Path to adapter
        
    Returns:
        Generated command
    """
    generator = HardGenerator(adapter_path=adapter_path)
    generator.load_adapter()
    return generator.generate(intent, kg_hints=kg_hints)


if __name__ == "__main__":
    # Example usage for testing
    print("="*70)
    print("HARD GENERATOR TEST")
    print("="*70)
    
    generator = HardGenerator()
    generator.load_adapter()
    
    test_cases = [
        "UDP SNMP brute force on 10.0.0.1",
        "Stealth scan with OS detection and maximum evasion",
        "IPv6 comprehensive scan with XML output",
        "Scan for web vulnerabilities on 192.168.1.0/24",
        "Fast scan with service version detection"
    ]
    
    for i, intent in enumerate(test_cases, 1):
        cmd = generator.generate(intent)
        print(f"\n{i}. Intent: {intent}")
        print(f"   Command: {cmd}")
    
    print("\n" + "="*70)
    print("✅ Test complete")