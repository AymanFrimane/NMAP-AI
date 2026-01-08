"""
NMAP-AI Gradio Demo Interface
Beautiful web interface for testing the NMAP-AI pipeline

Run with: python demo.py
Access at: http://localhost:7860
"""

import gradio as gr
import requests
from typing import Dict, Any, Tuple
import json

# API Configuration
API_URL = "http://localhost:8000"

# ============================================================================
# API Helper Functions
# ============================================================================

def check_api_status() -> Tuple[str, str, str, str]:
    """Check status of all services."""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            p1_status = "🟢 Online" if data["p1_comprehension"]["status"] == "online" else "🔴 Offline"
            p2_status = "🟢 Online" if data["p2_generator"]["status"] == "online" else "🔴 Offline"
            p4_status = "🟢 Online" if data["p4_validator"]["status"] == "online" else "🔴 Offline"
            overall = "✅ All Systems Operational" if all([
                data["p1_comprehension"]["status"] == "online",
                data["p2_generator"]["status"] == "online",
                data["p4_validator"]["status"] == "online"
            ]) else "⚠️ Some Systems Offline"
            return overall, p1_status, p2_status, p4_status
        else:
            return "❌ API Error", "❌", "❌", "❌"
    except Exception as e:
        return f"❌ API Not Running: {str(e)}", "❌", "❌", "❌"


def comprehend_query(query: str) -> Tuple[str, str, str]:
    """Call P1 comprehension endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/comprehend/",
            headers={"Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            intent = data.get("intent", "N/A")
            is_relevant = "✅ Yes" if data.get("is_relevant") else "❌ No"
            complexity = data.get("complexity") or "N/A"
            
            return intent, is_relevant, complexity
        else:
            return "Error", "Error", f"HTTP {response.status_code}"
    except Exception as e:
        return "Error", "Error", str(e)


def validate_command(command: str) -> Tuple[str, str, str, str, str]:
    """Call P4 validation endpoint."""
    try:
        response = requests.post(
            f"{API_URL}/api/validate",
            headers={"Content-Type": "application/json"},
            json={"command": command},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            valid = "✅ Valid" if data.get("valid") else "❌ Invalid"
            score = f"{data.get('score', 0):.2f}"
            errors = "\n".join(data.get("errors", [])) or "None"
            warnings = "\n".join(data.get("warnings", [])) or "None"
            feedback = data.get("feedback", "N/A")
            
            return valid, score, errors, warnings, feedback
        else:
            return "Error", "0", f"HTTP {response.status_code}", "", ""
    except Exception as e:
        return "Error", "0", str(e), "", ""


def generate_command(
    query: str,
    use_self_correction: bool = False,
    max_retries: int = 3
) -> Tuple[str, str, str, str, str, str]:
    """Call P2 generation endpoint (full pipeline)."""
    try:
        payload = {
            "query": query,
            "use_self_correction": use_self_correction,
            "max_retries": max_retries
        }
        
        response = requests.post(
            f"{API_URL}/api/generate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            command = data.get("command", "N/A")
            confidence = f"{data.get('confidence', 0):.2f}"
            
            validation = data.get("validation", {})
            valid = "✅ Valid" if validation.get("valid") else "❌ Invalid"
            errors = "\n".join(validation.get("errors", [])) or "None"
            warnings = "\n".join(validation.get("warnings", [])) or "None"
            
            metadata = data.get("metadata", {})
            meta_str = f"""
**Complexity:** {metadata.get('complexity', 'N/A')}
**Attempts:** {metadata.get('attempts', 1)}
**Corrected:** {'Yes' if metadata.get('corrected') else 'No'}
**Self-correction used:** {'Yes' if metadata.get('self_correction_used') else 'No'}
**P1 Available:** {'✅' if metadata.get('p1_available') else '❌'}
**P2 Available:** {'✅' if metadata.get('p2_available') else '❌'}
"""
            
            return command, confidence, valid, errors, warnings, meta_str
        else:
            return "Error", "0", f"HTTP {response.status_code}", "", "", ""
    except Exception as e:
        return "Error", "0", str(e), "", "", ""


# ============================================================================
# Gradio Interface
# ============================================================================

def create_interface():
    """Create the main Gradio interface."""
    
    with gr.Blocks(
        title="NMAP-AI Command Generator",
        theme=gr.themes.Soft()
    ) as demo:
        
        gr.Markdown("""
        # 🔍 NMAP-AI Command Generator
        
        **Natural Language → Nmap Commands with AI**
        
        Transform natural language queries into valid nmap commands using AI-powered generation, 
        validation, and self-correction.
        
        ---
        """)
        
        # ====================================================================
        # System Status
        # ====================================================================
        
        with gr.Accordion("📊 System Status", open=False):
            gr.Markdown("Check the status of all NMAP-AI services")
            
            status_btn = gr.Button("🔄 Refresh Status", variant="secondary")
            
            with gr.Row():
                overall_status = gr.Textbox(label="Overall Status", interactive=False)
                p1_status = gr.Textbox(label="P1 Comprehension", interactive=False)
                p2_status = gr.Textbox(label="P2 Generator", interactive=False)
                p4_status = gr.Textbox(label="P4 Validator", interactive=False)
            
            status_btn.click(
                fn=check_api_status,
                outputs=[overall_status, p1_status, p2_status, p4_status]
            )
        
        gr.Markdown("---")
        
        # ====================================================================
        # Main Tabs
        # ====================================================================
        
        with gr.Tabs():
            
            # ================================================================
            # Tab 1: Full Pipeline (Generate)
            # ================================================================
            
            with gr.TabItem("🚀 Generate Command (Full Pipeline)"):
                gr.Markdown("""
                ### Generate Nmap Commands from Natural Language
                
                Enter a natural language query and let the AI generate, validate, 
                and correct the nmap command for you.
                
                **Examples:**
                - "scan for SSH on 192.168.1.100"
                - "scan web servers on my network"
                - "ping scan 192.168.1.0/24"
                - "scan for SSH and HTTP on 10.0.0.1"
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gen_query = gr.Textbox(
                            label="Query",
                            placeholder="Enter your scan request in natural language...",
                            lines=2
                        )
                        
                        with gr.Row():
                            gen_self_correct = gr.Checkbox(
                                label="Use Self-Correction",
                                value=False,
                                info="Automatically retry and correct invalid commands"
                            )
                            gen_max_retries = gr.Slider(
                                minimum=1,
                                maximum=5,
                                value=3,
                                step=1,
                                label="Max Retries",
                                info="Maximum correction attempts"
                            )
                        
                        gen_btn = gr.Button("🎯 Generate Command", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        **Quick Tips:**
                        
                        🎯 **Services:** SSH, HTTP, FTP, etc.
                        
                        🌐 **Targets:** IP, subnet, hostname
                        
                        ⚡ **Speed:** "fast", "slow", "stealth"
                        
                        🔍 **Type:** "ping", "version", "OS"
                        """)
                
                gr.Markdown("### 📤 Results")
                
                with gr.Row():
                    gen_command = gr.Textbox(
                        label="Generated Command",
                        lines=2,
                        interactive=False
                    )
                
                with gr.Row():
                    gen_confidence = gr.Textbox(label="Confidence", interactive=False)
                    gen_valid = gr.Textbox(label="Validation", interactive=False)
                
                with gr.Row():
                    gen_errors = gr.Textbox(label="Errors", lines=3, interactive=False)
                    gen_warnings = gr.Textbox(label="Warnings", lines=3, interactive=False)
                
                gen_metadata = gr.Markdown(label="Metadata")
                
                gen_btn.click(
                    fn=generate_command,
                    inputs=[gen_query, gen_self_correct, gen_max_retries],
                    outputs=[gen_command, gen_confidence, gen_valid, gen_errors, gen_warnings, gen_metadata]
                )
                
                # Example buttons
                gr.Markdown("### 📝 Quick Examples")
                with gr.Row():
                    ex1 = gr.Button("SSH Scan", size="sm")
                    ex2 = gr.Button("Web Servers", size="sm")
                    ex3 = gr.Button("Ping Scan", size="sm")
                    ex4 = gr.Button("Multiple Services", size="sm")
                
                ex1.click(lambda: "scan for SSH on 192.168.1.100", outputs=gen_query)
                ex2.click(lambda: "scan web servers on 192.168.1.0/24", outputs=gen_query)
                ex3.click(lambda: "ping scan 192.168.1.0/24", outputs=gen_query)
                ex4.click(lambda: "scan for SSH and HTTP on 10.0.0.1", outputs=gen_query)
            
            # ================================================================
            # Tab 2: P1 Comprehension
            # ================================================================
            
            with gr.TabItem("🧠 P1 Comprehension"):
                gr.Markdown("""
                ### Analyze Query Understanding
                
                Test how the AI comprehends and classifies your natural language queries.
                
                - **Intent:** What the AI understands you want to do
                - **Relevance:** Whether the query is related to nmap/scanning
                - **Complexity:** EASY, MEDIUM, or HARD scan
                """)
                
                comp_query = gr.Textbox(
                    label="Query",
                    placeholder="Enter a query to analyze...",
                    lines=2
                )
                
                comp_btn = gr.Button("🔍 Analyze Query", variant="primary")
                
                with gr.Row():
                    comp_intent = gr.Textbox(label="Detected Intent", interactive=False)
                    comp_relevant = gr.Textbox(label="Relevant to Nmap?", interactive=False)
                    comp_complexity = gr.Textbox(label="Complexity Level", interactive=False)
                
                comp_btn.click(
                    fn=comprehend_query,
                    inputs=comp_query,
                    outputs=[comp_intent, comp_relevant, comp_complexity]
                )
                
                # Example buttons
                gr.Markdown("### 📝 Test Examples")
                with gr.Row():
                    comp_ex1 = gr.Button("EASY Query", size="sm")
                    comp_ex2 = gr.Button("MEDIUM Query", size="sm")
                    comp_ex3 = gr.Button("HARD Query", size="sm")
                    comp_ex4 = gr.Button("Irrelevant Query", size="sm")
                
                comp_ex1.click(lambda: "ping scan network", outputs=comp_query)
                comp_ex2.click(lambda: "scan for web servers with version detection", outputs=comp_query)
                comp_ex3.click(lambda: "aggressive scan with OS detection and scripts", outputs=comp_query)
                comp_ex4.click(lambda: "make me a sandwich", outputs=comp_query)
            
            # ================================================================
            # Tab 3: P4 Validation
            # ================================================================
            
            with gr.TabItem("✅ P4 Validation"):
                gr.Markdown("""
                ### Validate Nmap Commands
                
                Test command validation with syntax checking, conflict detection, 
                and safety analysis.
                """)
                
                val_command = gr.Textbox(
                    label="Nmap Command",
                    placeholder="Enter an nmap command to validate...",
                    lines=2
                )
                
                val_btn = gr.Button("🔍 Validate Command", variant="primary")
                
                with gr.Row():
                    val_valid = gr.Textbox(label="Valid?", interactive=False)
                    val_score = gr.Textbox(label="Validation Score", interactive=False)
                    val_feedback = gr.Textbox(label="Feedback", interactive=False)
                
                with gr.Row():
                    val_errors = gr.Textbox(label="Errors", lines=4, interactive=False)
                    val_warnings = gr.Textbox(label="Warnings", lines=4, interactive=False)
                
                val_btn.click(
                    fn=validate_command,
                    inputs=val_command,
                    outputs=[val_valid, val_score, val_errors, val_warnings, val_feedback]
                )
                
                # Example buttons
                gr.Markdown("### 📝 Test Examples")
                with gr.Row():
                    val_ex1 = gr.Button("Valid Command", size="sm")
                    val_ex2 = gr.Button("Invalid (No Target)", size="sm")
                    val_ex3 = gr.Button("Conflict (-sS + -sT)", size="sm")
                
                val_ex1.click(lambda: "nmap -sV -p 80,443 192.168.1.1", outputs=val_command)
                val_ex2.click(lambda: "nmap -sV", outputs=val_command)
                val_ex3.click(lambda: "nmap -sS -sT 192.168.1.1", outputs=val_command)
        
        # ====================================================================
        # Footer
        # ====================================================================
        
        gr.Markdown("""
        ---
        
        ### 📚 Documentation
        
        **Architecture:** P1 (Comprehension) → P2 (Generation) → P4 (Validation)
        
        **Technologies:** Python, FastAPI, T5+LoRA, Neo4j, scikit-learn
        
        **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
        
        **GitHub:** [NMAP-AI Project](https://github.com/yourusername/NMAP-AI)
        
        ---
        
        Made with ❤️ using Gradio
        """)
    
    return demo


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🚀 NMAP-AI Gradio Demo")
    print("="*60)
    print()
    print("Starting Gradio interface...")
    print(f"API URL: {API_URL}")
    print()
    print("📝 Make sure the API is running:")
    print("   python -m uvicorn api.main:app --reload --port 8000")
    print()
    print("="*60)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ API is running!")
        else:
            print("⚠️  API responded but with error")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        print("   Please start the API first!")
    
    print("="*60)
    print()
    
    # Create and launch demo
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )