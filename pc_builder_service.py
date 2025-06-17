#!/usr/bin/env python3
"""
PC Builder Demo Service - Multiple Agent Architecture

This service provides specialized PC building assistance through three dedicated agents:
- Triage Agent (/) - Routes customers to appropriate specialists
- Sales Agent (/sales) - Handles product recommendations and purchases  
- Support Agent (/support) - Provides technical support and troubleshooting

Key Feature: Uses SignalWire's swml_transfer skill with required_fields for automatic
context preservation. The skill ensures both the customer's name and a comprehensive summary
are collected before transferring and makes them available via ${global_data.call_data.user_name}
and ${global_data.call_data.summary} to the receiving agent.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from signalwire_agents import AgentBase, AgentServer
from signalwire_agents.core.function_result import SwaigFunctionResult
from signalwire_agents.core.logging_config import get_logger

# Set up logger for this module
logger = get_logger(__name__)

# Define the Triage Agent (root route)
class TriageAgent(AgentBase):
    def __init__(self):
        super().__init__(
            name="PC Builder Triage Agent",
            route="/",  # Root route
            host="0.0.0.0",
            port=3001
        )
        
        # Configure prompt using POM
        self._configure_prompt()
        
        # Set up dynamic configuration for URL-dependent tools
        self.set_dynamic_config_callback(self.configure_transfer_tools)
    
    def configure_transfer_tools(self, query_params, body_params, headers, agent):
        """
        DYNAMIC CONFIGURATION - Called fresh for every request
        
        This uses the swml_transfer skill with correct URLs after proxy detection is available.
        
        Args:
            query_params: Query string parameters from the request
            body_params: POST body parameters (empty for GET requests)
            headers: HTTP headers from the request
            agent: EphemeralAgentConfig object to configure
        """
        # Build URLs with proper proxy detection
        sales_url = self.get_full_url(include_auth=True).rstrip('/') + "/sales"
        support_url = self.get_full_url(include_auth=True).rstrip('/') + "/support"
        
        # Configure transfers using swml_transfer skill
        agent.add_skill("swml_transfer", {
            "tool_name": "transfer_to_specialist",
            "description": "Transfer to sales or support specialist with conversation summary",
            "parameter_name": "specialist_type",
            "parameter_description": "The type of specialist to transfer to (sales or support)",
            "required_fields": {
                "user_name": "The customer's name",
                "summary": "A comprehensive summary of the conversation so far, including what the customer needs help with"
            },
            "transfers": {
                "/sales/i": {
                    "url": sales_url,
                    "message": "Perfect! Let me transfer you to our sales specialist right away.",
                    "return_message": "The call with the sales specialist is complete. How else can I help you?",
                    "post_process": True
                },
                "/support/i": {
                    "url": support_url,
                    "message": "I'll connect you with our technical support specialist right away.",
                    "return_message": "The call with the support specialist is complete. How else can I help you?",
                    "post_process": True
                }
            },
            "default_message": "I can transfer you to either our sales or support specialist. Which would you prefer?"
        })
    
    def _configure_prompt(self):
        """Configure the prompt for the triage agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are a virtual assistant for PC Builder Pro, greeting customers and directing them to the right specialist."
        )
        
        self.prompt_add_section(
            "Your Tasks",
            body="Guide customers through the initial triage process.",
            bullets=[
                "Greet the customer warmly",
                "Ask for their name",
                "Determine if they need sales (buying/building) or support (technical issues)",
                "Get a brief description of what they need help with",
                "Prepare a comprehensive summary before transferring",
                "Use transfer_to_specialist with both the destination and summary"
            ]
        )
        
        self.prompt_add_section(
            "Important",
            body="Follow these key guidelines for effective triage:",
            bullets=[
                "Always get the customer's name first",
                "Ask clarifying questions to determine sales vs support",
                "The transfer_to_specialist function requires both specialist_type AND summary",
                "Include customer name, their needs, and reason for transfer in the summary"
            ]
        )
        
        self.prompt_add_section(
            "Summary Example",
            body="When transferring, provide a summary like: 'Customer John Smith is interested in building a gaming PC with a budget of $2000. He needs help selecting compatible components and wants recommendations for the best performance within his budget.'"
        )
    
    def _check_basic_auth(self, request) -> bool:
        """Override to disable authentication requirement"""
        return True


# Define the Sales Agent
class SalesAgent(AgentBase):
    def __init__(self):
        super().__init__(
            name="PC Builder Sales Specialist",
            route="/sales",
            host="0.0.0.0", 
            port=3001
        )
        
        # Configure prompt using POM
        self._configure_prompt()
        
        # Add search capability for sales knowledge
        self.add_skill("native_vector_search", {
            "tool_name": "search_sales_knowledge",
            "description": "Search sales and product information",
            "index_file": "sales_knowledge.swsearch",
            "count": 3
        })
        
        # Define sales-specific functions
        @self.tool("create_build_recommendation", description="Create a custom PC build recommendation")
        async def create_build_recommendation(budget: str, use_case: str, preferences: str):
            return SwaigFunctionResult(f"Based on your ${budget} budget for {use_case}, I recommend: [Custom build details would be generated here based on current market data and your preferences: {preferences}]")
        
        @self.tool("check_component_compatibility", description="Check if PC components are compatible")
        async def check_component_compatibility(components: str):
            return SwaigFunctionResult(f"Compatibility check for: {components} - [Detailed compatibility analysis would be performed here]")
    
    def _configure_prompt(self):
        """Configure the prompt for the sales agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are a specialized PC building sales consultant for PC Builder Pro."
        )
        
        self.prompt_add_section(
            "Transfer Context",
            body="If this call was transferred to you, important context is available. Check ${global_data.call_data.user_name} for the customer's name and ${global_data.call_data.summary} for conversation details. Always greet the customer by name and acknowledge the transfer context."
        )
        
        self.prompt_add_section(
            "Your Expertise",
            body="Areas of specialization:",
            bullets=[
                "Custom PC builds for all budgets",
                "Component compatibility and optimization",
                "Performance recommendations",
                "Price/performance analysis",
                "Current market trends"
            ]
        )
        
        self.prompt_add_section(
            "Your Tasks",
            body="Complete sales process workflow:",
            bullets=[
                "Check if ${global_data.call_data.user_name} and ${global_data.call_data.summary} exist and review them",
                "Understand their specific PC building requirements",
                "Ask about budget, intended use, and preferences",
                "Search knowledge base for current product info",
                "Create customized build recommendations",
                "Help with component selection and compatibility"
            ]
        )
        
        self.prompt_add_section(
            "Tools Available",
            body="Use these tools to assist customers:",
            bullets=[
                "search_sales_knowledge: Find current product information",
                "create_build_recommendation: Generate custom build suggestions",
                "check_component_compatibility: Verify component compatibility"
            ]
        )
        
        self.prompt_add_section(
            "Important",
            body="Key guidelines for sales interactions:",
            bullets=[
                "If available, use ${global_data.call_data.user_name} to greet by name and ${global_data.call_data.summary} to understand context",
                "Ask clarifying questions about their specific requirements",
                "Use search to get current pricing and availability",
                "Provide detailed explanations for recommendations"
            ]
        )
    
    def _check_basic_auth(self, request) -> bool:
        """Override to disable authentication requirement"""
        return True


# Define the Support Agent  
class SupportAgent(AgentBase):
    def __init__(self):
        super().__init__(
            name="PC Builder Support Specialist",
            route="/support",
            host="0.0.0.0",
            port=3001
        )
        
        # Configure prompt using POM
        self._configure_prompt()
        
        # Add search capability for support knowledge
        self.add_skill("native_vector_search", {
            "tool_name": "search_support_knowledge", 
            "description": "Search technical support and troubleshooting information",
            "index_file": "support_knowledge.swsearch",
            "count": 3
        })
        
        # Define support-specific functions
        @self.tool("diagnose_hardware_issue", description="Help diagnose PC hardware problems")
        async def diagnose_hardware_issue(symptoms: str, system_specs: str):
            return SwaigFunctionResult(f"For symptoms '{symptoms}' on system '{system_specs}': [Diagnostic steps and potential solutions would be provided here]")
        
        @self.tool("create_support_ticket", description="Create a support ticket for complex issues")
        async def create_support_ticket(issue_description: str, customer_info: str, priority: str):
            ticket_id = f"SUP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            return SwaigFunctionResult(f"Support ticket {ticket_id} created for: {issue_description}. Priority: {priority}. We'll follow up within 24 hours.")
    
    def _configure_prompt(self):
        """Configure the prompt for the support agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are a specialized technical support specialist for PC Builder Pro."
        )
        
        self.prompt_add_section(
            "Transfer Context",
            body="If this call was transferred to you, important context is available. Check ${global_data.call_data.user_name} for the customer's name and ${global_data.call_data.summary} for conversation details. Always greet the customer by name and acknowledge the transfer context."
        )
        
        self.prompt_add_section(
            "Your Expertise",
            body="Areas of technical specialization:",
            bullets=[
                "Hardware troubleshooting and diagnostics",
                "Software compatibility issues",
                "System optimization and performance",
                "Component failure analysis",
                "Warranty and repair processes"
            ]
        )
        
        self.prompt_add_section(
            "Your Tasks",
            body="Complete support process workflow:",
            bullets=[
                "Check if ${global_data.call_data.user_name} and ${global_data.call_data.summary} exist and review them",
                "Understand their specific technical problems",
                "Search knowledge base for solutions",
                "Guide through diagnostic steps",
                "Provide troubleshooting solutions",
                "Create support tickets for complex issues"
            ]
        )
        
        self.prompt_add_section(
            "Tools Available",
            body="Use these tools to resolve issues:",
            bullets=[
                "search_support_knowledge: Find technical solutions",
                "diagnose_hardware_issue: Analyze hardware problems",
                "create_support_ticket: Escalate complex issues"
            ]
        )
        
        self.prompt_add_section(
            "Important",
            body="Key guidelines for support interactions:",
            bullets=[
                "If available, use ${global_data.call_data.user_name} to greet by name and ${global_data.call_data.summary} to understand context",
                "Ask detailed questions about the problem",
                "Use search to find known solutions",
                "Guide step-by-step through troubleshooting",
                "Be patient and thorough"
            ]
        )
    
    def _check_basic_auth(self, request) -> bool:
        """Override to disable authentication requirement"""
        return True


def create_pc_builder_app(host: str = "0.0.0.0", port: int = 3001, log_level: str = "info") -> AgentServer:
    """
    Create and configure the PC Builder application with three specialized agents
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to  
        log_level: Logging level (debug, info, warning, error, critical)
    
    Returns:
        Configured AgentServer with all three agents registered
    """
    # Create the server
    server = AgentServer(host=host, port=port, log_level=log_level)
    
    # Create and register Triage Agent (root)
    triage = TriageAgent()
    server.register(triage, "/")
    
    # Create and register Sales Agent
    sales = SalesAgent()
    server.register(sales, "/sales")
    
    # Create and register Support Agent
    support = SupportAgent()
    server.register(support, "/support")
    
    # Add a root endpoint to show available agents
    @server.app.get("/info")
    async def info():
        return {
            "message": "PC Builder Pro - Multi-Agent Service",
            "agents": {
                "triage": {
                    "endpoint": "/",
                    "description": "Greets customers and routes to specialists with automatic context collection"
                },
                "sales": {
                    "endpoint": "/sales",
                    "description": "PC building sales and recommendations specialist"
                },
                "support": {
                    "endpoint": "/support", 
                    "description": "Technical support and troubleshooting specialist"
                }
            },
            "features": {
                "context_sharing": "Uses swml_transfer skill with user_name and summary requirements",
                "pom_prompts": "Structured prompts using Prompt Object Model",
                "summary_access": "Transfer context available via ${global_data.call_data.user_name} and ${global_data.call_data.summary}",
                "multi_agent": "Three specialized agents working together seamlessly"
            },
            "usage": {
                "triage_swml": f"GET/POST http://{host}:{port}/",
                "sales_swml": f"GET/POST http://{host}:{port}/sales",
                "support_swml": f"GET/POST http://{host}:{port}/support"
            }
        }
    
    return server


def lambda_handler(event, context):
    """AWS Lambda entry point - delegates to universal server run method"""
    server = create_pc_builder_app()
    return server.run(event, context)


if __name__ == "__main__":
    logger.info("Starting PC Builder Pro Multi-Agent Service")
    logger.info("=" * 60)
    logger.info("Triage Agent: http://localhost:3001/")
    logger.info("  - Greets customers and routes to specialists")
    logger.info("  - Requires customer name and comprehensive summary before transfer")
    logger.info("  - Uses swml_transfer skill for seamless handoffs")
    logger.info("")
    logger.info("Sales Agent: http://localhost:3001/sales") 
    logger.info("  - Custom PC build recommendations")
    logger.info("  - Component compatibility checking")
    logger.info("  - Pricing and performance analysis")
    logger.info("  - Accesses customer name via ${global_data.call_data.user_name}")
    logger.info("  - Accesses transfer summary via ${global_data.call_data.summary}")
    logger.info("")
    logger.info("Support Agent: http://localhost:3001/support")
    logger.info("  - Technical troubleshooting and diagnostics")
    logger.info("  - Hardware issue resolution")
    logger.info("  - Support ticket creation")
    logger.info("  - Accesses customer name via ${global_data.call_data.user_name}")
    logger.info("  - Accesses transfer summary via ${global_data.call_data.summary}")
    logger.info("")
    logger.info("Service Info: http://localhost:3001/info")
    logger.info("=" * 60)
    
    logger.info("Features:")
    logger.info("✔ Multi-agent architecture with automatic context sharing")
    logger.info("✔ swml_transfer skill with required user_name and summary fields")
    logger.info("✔ Native vector search for knowledge bases")
    logger.info("✔ POM-style prompts for better structure and maintainability")
    logger.info("✔ Automatic name and summary preservation across transfers")
    logger.info("✔ Specialized expertise per agent")
    logger.info("")
    logger.info("How it works:")
    logger.info("1. Triage agent uses swml_transfer skill with user_name and summary requirements")
    logger.info("2. The skill automatically prompts for customer name and comprehensive summary before transfer") 
    logger.info("3. Name and summary are automatically available to receiving agent")
    logger.info("4. Sales/Support agents access context via ${global_data.call_data.user_name} and ${global_data.call_data.summary}")
    
    # Create and run the server
    server = create_pc_builder_app()
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down PC Builder Pro service...") 
