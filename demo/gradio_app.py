"""
NMAP-AI Gradio Demo Interface
Person 4's responsibility

Beautiful UI for demonstrating the NMAP-AI system
Calls the unified /generate endpoint and displays results
"""

import gradio as gr
import requests
import os
from typing import Tuple
import json

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ============================================================================
# API Functions
# ============================================================================

def test_api_connection() -> str:
    """
    Test connection to the API
    
    Returns:
        Status message
    """
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return "✅ API is online and ready!"
        else:
            return f"⚠️  API responded with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return f"❌ Cannot connect to API at {API_URL}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def generate_nmap_command(query: str) -> Tuple[str, str, str, str, str]:
    """
    Call the unified /generate endpoint and return formatted results
    
    Args:
        query: Natural language query
        
    Returns:
        (command, confidence, explanation, validation_status, metadata)
    """
    if not query.strip():
        return "", "0.00", "Please enter a query", "⚠️  No input", ""
    
    try:
        # Call unified generation endpoint
        response = requests.post(
            f"{API_URL}/api/generate",
            json={"query": query},
            timeout=20  # Longer timeout for generation
        )
        
        if response.status_code != 200:
            return (
                "",
                "0.00",
                f"API Error: {response.status_code} - {response.text[:200]}",
                "❌ Error",
                ""
            )
        
        result = response.json()
        
        # Extract results
        command = result.get('command', 'No command generated')
        confidence = result.get('confidence', 0.0)
        explanation = result.get('explanation', 'No explanation provided')
        validation = result.get('validation', {})
        metadata = result.get('metadata', {})
        
        # Format validation status
        if validation.get('is_valid') or validation.get('valid'):
            val_status = "✅ Valid"
            score = validation.get('score', 0.0)
            val_status += f" (score: {score:.2f})"
            
            if validation.get('warnings'):
                val_status += f"\n⚠️  {len(validation['warnings'])} warning(s)"
        else:
            val_status = "❌ Invalid"
            if validation.get('errors'):
                val_status += f"\n❌ {len(validation['errors'])} error(s)"
        
        # Format errors and warnings in explanation
        details = []
        if validation.get('errors'):
            details.append("\n🔴 Errors:")
            for error in validation['errors'][:3]:  # Show first 3
                details.append(f"  • {error}")
            if len(validation['errors']) > 3:
                details.append(f"  • ... and {len(validation['errors']) - 3} more")
        
        if validation.get('warnings'):
            details.append("\n🟡 Warnings:")
            for warning in validation['warnings'][:3]:  # Show first 3
                details.append(f"  • {warning}")
            if len(validation['warnings']) > 3:
                details.append(f"  • ... and {len(validation['warnings']) - 3} more")
        
        if details:
            explanation += "\n\n" + "\n".join(details)
        
        # Format metadata
        meta_str = f"Complexity: {metadata.get('complexity', 'N/A')}\n"
        meta_str += f"Attempts: {metadata.get('attempts', 1)}\n"
        meta_str += f"Corrected: {'Yes' if metadata.get('corrected') else 'No'}"
        
        return (
            command,
            f"{confidence:.2f}",
            explanation,
            val_status,
            meta_str
        )
        
    except requests.exceptions.Timeout:
        return (
            "",
            "0.00",
            "⏱️  Request timed out. The query might be too complex.",
            "⏱️  Timeout",
            ""
        )
    except requests.exceptions.ConnectionError:
        return (
            "",
            "0.00",
            f"🔌 Cannot connect to API at {API_URL}. Ensure the API is running:\n"
            f"  docker-compose up -d api",
            "🔌 Connection Error",
            ""
        )
    except Exception as e:
        return (
            "",
            "0.00",
            f"❌ Unexpected error: {str(e)}",
            "❌ Error",
            ""
        )


def validate_only(command: str) -> Tuple[str, str]:
    """
    Validate an existing nmap command
    
    Args:
        command: Nmap command to validate
        
    Returns:
        (validation_status, explanation)
    """
    if not command.strip():
        return "⚠️  No input", "Please enter a command to validate"
    
    try:
        response = requests.post(
            f"{API_URL}/api/validate",
            json={"command": command},
            timeout=10
        )
        
        if response.status_code != 200:
            return "❌ Error", f"API Error: {response.status_code}"
        
        result = response.json()
        
        # Format validation status
        if result.get('is_valid') or result.get('valid'):
            status = f"✅ Valid (score: {result.get('score', 0):.2f})"
        else:
            status = "❌ Invalid"
        
        # Format explanation
        explanation = result.get('feedback', '')
        
        if result.get('errors'):
            explanation += "\n\n🔴 Errors:\n"
            for error in result['errors']:
                explanation += f"  • {error}\n"
        
        if result.get('warnings'):
            explanation += "\n🟡 Warnings:\n"
            for warning in result['warnings']:
                explanation += f"  • {warning}\n"
        
        return status, explanation
        
    except Exception as e:
        return "❌ Error", str(e)


# ============================================================================
# Gradio Interface
# ============================================================================

# Custom CSS for better styling
custom_css = """
.gradio-container {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    max-width: 1200px;
    margin: auto;
}

.command-box {
    font-family: 'Fira Code', 'Courier New', monospace;
    background-color: #f5f5f5;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #ddd;
}

.result-box {
    padding: 10px;
    border-radius: 4px;
    margin: 5px 0;
}

footer {
    display: none !important;
}
"""

# Create Gradio Interface
with gr.Blocks(title="NMAP-AI", css=custom_css, theme=gr.themes.Soft()) as demo:
    
    # Header
    gr.Markdown(
        """
        # 🚀 NMAP-AI: Natural Language to Nmap Commands
        
        Transform natural language descriptions into valid, optimized Nmap commands.
        
        **Powered by:** T5 LoRA, Knowledge Graph RAG, Self-Correction, and Advanced Validation
        """
    )
    
    # API Status
    with gr.Row():
        api_status = gr.Textbox(
            label="📡 API Status",
            value=test_api_connection(),
            interactive=False,
            lines=1
        )
        refresh_btn = gr.Button("🔄 Refresh", size="sm", scale=0)
    
    gr.Markdown("---")
    
    # Main Interface - Generation
    gr.Markdown("## 🎯 Generate Nmap Command")
    
    with gr.Row():
        with gr.Column(scale=1):
            query_input = gr.Textbox(
                label="Your Intent (Natural Language)",
                placeholder="Example: Scan web servers with version detection on 192.168.1.0/24",
                lines=4,
                info="Describe what you want to scan in plain English"
            )
            
            generate_btn = gr.Button(
                "🎯 Generate Command",
                variant="primary",
                size="lg"
            )
        
        with gr.Column(scale=1):
            command_output = gr.Textbox(
                label="📝 Generated Nmap Command",
                lines=3,
                elem_classes=["command-box"],
                info="Copy this command to your terminal"
            )
            
            with gr.Row():
                confidence_output = gr.Textbox(
                    label="🎯 Confidence",
                    scale=1,
                    lines=1
                )
                validation_output = gr.Textbox(
                    label="✓ Validation",
                    scale=1,
                    lines=2
                )
            
            explanation_output = gr.Textbox(
                label="💡 Explanation & Details",
                lines=6,
                info="Why this command was generated and any warnings"
            )
            
            metadata_output = gr.Textbox(
                label="📊 Metadata",
                lines=3,
                info="Technical details about generation"
            )
    
    # Examples
    gr.Markdown("---")
    gr.Markdown("## 💡 Example Queries")
    
    gr.Examples(
        examples=[
            # EASY
            "Ping scan my entire network 192.168.1.0/24",
            "Quick scan of 192.168.1.1",
            "Check if host 10.0.0.1 is up",
            
            # MEDIUM
            "Scan all ports on 192.168.1.1",
            "Find web servers on my network 10.0.0.0/24",
            "Scan ports 80,443,8080 with version detection on example.com",
            "Detect SSH servers with version info on 192.168.1.0/24",
            
            # HARD
            "Comprehensive security audit with OS detection and vulnerability scripts on 192.168.1.0/24",
            "Stealthy UDP scan for DNS and SNMP on my network",
            "Fast aggressive scan with all default scripts on 192.168.1.100",
            "Full port scan with service detection and aggressive timing on target.com",
        ],
        inputs=query_input,
        label="Click an example to try it"
    )
    
    gr.Markdown("---")
    
    # Validation Tab
    gr.Markdown("## ✓ Validate Existing Command")
    
    with gr.Row():
        validate_input = gr.Textbox(
            label="Nmap Command to Validate",
            placeholder="nmap -sV -p 80,443 192.168.1.1",
            lines=2
        )
        validate_btn = gr.Button("✓ Validate", variant="secondary")
    
    with gr.Row():
        validate_status = gr.Textbox(label="Status", scale=1)
        validate_explanation = gr.Textbox(label="Details", scale=2, lines=4)
    
    # Footer
    gr.Markdown("---")
    gr.Markdown(
        """
        ### ⚠️  Important Notes
        
        - This tool is for **educational purposes** and **authorized penetration testing only**
        - Always ensure you have **permission** before scanning networks
        - Some commands may require **root/sudo privileges**
        - Generated commands are validated but should be **reviewed before execution**
        
        ### 🛠️ Tech Stack
        
        **Backend:** FastAPI • Neo4j • Python 3.11  
        **ML Models:** T5-small (LoRA) • Sentence-BERT • scikit-learn  
        **Validation:** Syntax • Conflict • Safety • Self-Correction  
        **DevOps:** Docker • GitHub Actions CI/CD
        
        ### 📚 Resources
        
        - [Nmap Official Documentation](https://nmap.org/book/man.html)
        - [API Documentation](http://localhost:8000/docs)
        - [Neo4j Browser](http://localhost:7474)
        """
    )
    
    # Event Handlers
    generate_btn.click(
        fn=generate_nmap_command,
        inputs=query_input,
        outputs=[
            command_output,
            confidence_output,
            explanation_output,
            validation_output,
            metadata_output
        ]
    )
    
    validate_btn.click(
        fn=validate_only,
        inputs=validate_input,
        outputs=[validate_status, validate_explanation]
    )
    
    refresh_btn.click(
        fn=test_api_connection,
        outputs=api_status
    )


# ============================================================================
# Launch Application
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Starting NMAP-AI Gradio Interface")
    print("=" * 70)
    print(f"\n📡 API URL: {API_URL}")
    print(f"🌐 Gradio will be available at: http://localhost:7860")
    print(f"\n✨ Interface features:")
    print("   • Natural language to Nmap command generation")
    print("   • Real-time validation")
    print("   • Confidence scoring")
    print("   • Example queries")
    print("\n" + "=" * 70 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True,
        show_api=False
    )
