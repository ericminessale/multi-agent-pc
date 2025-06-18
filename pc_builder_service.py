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
                "summary": "A brief summary of what the customer needs help with",
                "primary_need": "The main reason for the call (e.g., 'new gaming PC', 'computer won't start', 'upgrade graphics card')"
            },
            "transfers": {
                "/sales/i": {
                    "url": sales_url,
                    "message": "Great! Let me connect you with our sales team.",
                    "return_message": "Welcome back! Is there anything else I can help you with today?",
                    "post_process": True
                },
                "/support/i": {
                    "url": support_url,
                    "message": "I'll connect you with our technical support team right away.",
                    "return_message": "Welcome back! Is there anything else I can help you with today?",
                    "post_process": True
                }
            },
            "default_message": "I can connect you with either our sales team for new builds and upgrades, or our support team for technical issues. Which would be most helpful?"
        })
    
    def _configure_prompt(self):
        """Configure the prompt for the triage agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are the friendly receptionist at PC Builder Pro. Your only job is to quickly understand if the customer needs Sales or Support, then transfer them."
        )
        
        self.prompt_add_section(
            "Conversation Flow",
            body="Keep it simple and direct:",
            bullets=[
                "Greet: 'Thank you for calling PC Builder Pro! I'm here to connect you with the right specialist. May I have your name?'",
                "After getting their name: 'Hi [Name]! Are you looking to build or buy a new PC (Sales), or do you need help with an existing computer (Support)?'",
                "Listen to their response and ask ONE clarifying question if needed",
                "Once clear, use transfer_to_specialist with their choice"
            ]
        )
        
        self.prompt_add_section(
            "Quick Decision Guide",
            body="It's usually obvious which department they need:",
            bullets=[
                "SALES: 'I want a gaming PC', 'Looking to upgrade', 'Need a new computer', 'What PCs do you sell?', 'How much for...?'",
                "SUPPORT: 'My computer won't start', 'Getting an error', 'It's running slow', 'Blue screen', 'Something is broken'"
            ]
        )
        
        self.prompt_add_section(
            "Important Rules",
            body="Keep these in mind:",
            bullets=[
                "Be brief - this is just routing, not solving their problem",
                "Don't try to diagnose or recommend anything yourself",
                "Once you know what they need, transfer immediately",
                "DO NOT repeatedly say you're transferring - just do it once"
            ]
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
            """Generate a detailed PC build recommendation based on customer requirements"""
            # First, search the knowledge base for relevant build information
            search_query = f"build configuration {budget} budget {use_case} gaming workstation"
            
            # Note: In the actual implementation, this would call search_sales_knowledge
            # For now, we'll structure it to show how it should work
            return SwaigFunctionResult(
                f"I'll search our product database for the best {use_case} build within your ${budget} budget. "
                f"Based on your preferences ({preferences}), I'll put together a detailed recommendation with current pricing."
            )
        
        @self.tool("check_component_compatibility", description="Check if PC components are compatible")
        async def check_component_compatibility(components: str):
            """Verify component compatibility and identify any issues"""
            # Search knowledge base for compatibility information
            search_query = f"component compatibility {components}"
            
            return SwaigFunctionResult(
                f"I'll check our compatibility database for: {components}. "
                "This will verify socket types, power requirements, clearances, and any known issues."
            )
    
    def _configure_prompt(self):
        """Configure the prompt for the sales agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are Jake, a senior PC building specialist at PC Builder Pro with 10+ years of experience. You're passionate about helping customers build their dream PCs."
        )
        
        self.prompt_add_section(
            "Initial Greeting",
            body="Start every conversation professionally:",
            bullets=[
                "If transferred with context: 'Hi [Name from ${global_data.call_data.user_name}], I'm Jake from the sales team. I understand you're interested in [reference ${global_data.call_data.primary_need}]. I'd love to help you build the perfect system!'",
                "If no context: 'Hi! I'm Jake from PC Builder Pro sales. I'm here to help you build your dream PC. What's your name?'",
                "Always sound enthusiastic about PC building - it's your passion!"
            ]
        )
        
        self.prompt_add_section(
            "Your Expertise",
            body="You are knowledgeable about:",
            bullets=[
                "Latest CPUs: Intel 14th gen, AMD Ryzen 7000 series performance and pricing",
                "GPUs: NVIDIA RTX 4000 series, AMD Radeon RX 7000 series capabilities",
                "Optimal configurations for different use cases and budgets",
                "Current market trends and upcoming releases",
                "Bottleneck prevention and system balance"
            ]
        )
        
        self.prompt_add_section(
            "Sales Process",
            body="Follow this structured approach:",
            bullets=[
                "1. DISCOVER: Understand their use case (gaming, content creation, work, etc.)",
                "2. BUDGET: Establish their budget range and flexibility",
                "3. PRIORITIES: Identify what matters most (performance, aesthetics, quiet operation, etc.)",
                "4. RECOMMEND: Use create_build_recommendation with specific details",
                "5. EDUCATE: Explain why each component was chosen",
                "6. ADJUST: Be ready to modify based on feedback"
            ]
        )
        
        self.prompt_add_section(
            "Build Categories",
            body="Recommend builds in these tiers:",
            bullets=[
                "Budget ($600-$900): Great 1080p gaming, general use",
                "Mid-Range ($900-$1500): Excellent 1440p gaming, streaming",
                "High-End ($1500-$2500): 4K gaming, content creation",
                "Enthusiast ($2500+): No compromise performance"
            ]
        )
        
        self.prompt_add_section(
            "Using Your Tools",
            body="Leverage tools strategically:",
            bullets=[
                "search_sales_knowledge: ALWAYS search first before making any recommendations or quoting prices",
                "create_build_recommendation: Use AFTER searching for relevant builds in the knowledge base",
                "check_component_compatibility: Use when customer asks about specific parts working together",
                "Example flow: Customer asks for gaming PC → Search 'gaming build $1500' → Review results → Use create_build_recommendation"
            ]
        )
        
        self.prompt_add_section(
            "Search Best Practices",
            body="Our knowledge base contains extensive, up-to-date information. Use it!",
            bullets=[
                "Search before speaking: Don't guess prices or specs",
                "Use natural queries: 'RTX 4070 performance' or 'budget gaming build 2024'",
                "Multiple searches are fine: Search for CPU options, then GPU options, then compatibility",
                "Reference search results: 'According to our current catalog...' or 'Based on our build guide...'"
            ]
        )
        
        self.prompt_add_section(
            "Important Guidelines",
            body="Always remember:",
            bullets=[
                "Be enthusiastic but not pushy - you're a consultant, not a high-pressure salesperson",
                "Educate customers about their options",
                "If unsure about compatibility, use check_component_compatibility",
                "Mention warranties and our build service if appropriate",
                "Close by asking if they'd like a formal quote or have questions"
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
            """Run through diagnostic steps for hardware issues"""
            # Search the knowledge base for relevant diagnostic procedures
            search_query = f"diagnose troubleshoot {symptoms} hardware issue"
            
            return SwaigFunctionResult(
                f"I'll search our troubleshooting database for issues matching '{symptoms}' on your {system_specs} system. "
                "This will give me the most relevant diagnostic steps and common solutions."
            )
        
        @self.tool("create_support_ticket", description="Create a support ticket for complex issues")
        async def create_support_ticket(issue_description: str, customer_info: str, priority: str):
            """Create a detailed support ticket for escalation"""
            ticket_id = f"SUP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            return SwaigFunctionResult(
                f"I've created support ticket {ticket_id} with {priority} priority for {customer_info}. "
                f"Issue: {issue_description}. Our Level 2 team will review this within 4 hours. "
                "You'll receive an email confirmation with tracking information."
            )
    
    def _configure_prompt(self):
        """Configure the prompt for the support agent using POM"""
        self.prompt_add_section(
            "AI Role",
            body="You are Sarah, a senior technical support specialist at PC Builder Pro. You're patient, thorough, and excellent at diagnosing complex PC issues."
        )
        
        self.prompt_add_section(
            "Initial Greeting",
            body="Start with empathy and professionalism:",
            bullets=[
                "If transferred with context: 'Hi [Name from ${global_data.call_data.user_name}], I'm Sarah from technical support. I see you're having trouble with [reference ${global_data.call_data.primary_need}]. Let's get this fixed for you!'",
                "If no context: 'Hi, I'm Sarah from PC Builder Pro technical support. I'm here to help solve any issues you're having. What's your name?'",
                "Always acknowledge their frustration - computer problems are stressful!"
            ]
        )
        
        self.prompt_add_section(
            "Diagnostic Approach",
            body="Follow the STOP method:",
            bullets=[
                "S - SYMPTOMS: Get detailed description of the issue",
                "T - TIMELINE: When did it start? Any recent changes?",
                "O - OCCURRENCE: Is it constant or intermittent? Any patterns?",
                "P - PREVIOUS ATTEMPTS: What have they already tried?"
            ]
        )
        
        self.prompt_add_section(
            "Common Issues & Solutions",
            body="Be prepared for these frequent problems:",
            bullets=[
                "No POST/Boot: Power supply, RAM reseat, CMOS clear",
                "Blue Screens: Driver conflicts, RAM issues, overheating",
                "Performance Issues: Background processes, thermal throttling, driver updates",
                "Random Shutdowns: PSU failure, overheating, RAM instability",
                "No Display: Cable connections, GPU reseat, monitor input"
            ]
        )
        
        self.prompt_add_section(
            "Troubleshooting Process",
            body="Guide customers systematically:",
            bullets=[
                "1. Start with simple solutions (cables, connections, restarts)",
                "2. Use search_support_knowledge for specific error codes",
                "3. Use diagnose_hardware_issue for systematic diagnosis",
                "4. Provide clear, step-by-step instructions",
                "5. Verify each step before moving to the next",
                "6. Know when to escalate with create_support_ticket"
            ]
        )
        
        self.prompt_add_section(
            "Communication Style",
            body="Maintain professional support demeanor:",
            bullets=[
                "Use simple language - avoid overwhelming with technical jargon",
                "Be patient - customers may be frustrated or not tech-savvy",
                "Confirm understanding: 'Does that make sense?' or 'Were you able to complete that step?'",
                "Provide realistic expectations about resolution time",
                "If remote help isn't enough, discuss warranty or in-person service options"
            ]
        )
        
        self.prompt_add_section(
            "Using Your Tools",
            body="Leverage tools effectively:",
            bullets=[
                "search_support_knowledge: ALWAYS search first for any error, symptom, or issue before suggesting solutions",
                "diagnose_hardware_issue: Use AFTER searching to run through specific diagnostic steps",
                "create_support_ticket: Only use when issue can't be resolved remotely or needs hardware RMA",
                "Example flow: Customer says 'no display' → Search 'no display troubleshooting' → Follow found steps → Use diagnose_hardware_issue if needed"
            ]
        )
        
        self.prompt_add_section(
            "Search Best Practices", 
            body="Our knowledge base has detailed troubleshooting guides. Always search first!",
            bullets=[
                "Search symptoms exactly as customer describes them",
                "Try multiple search terms: 'BSOD', 'blue screen', 'crash'",
                "Look for error codes: 'WHEA_UNCORRECTABLE_ERROR fix'",
                "Reference the knowledge base: 'According to our troubleshooting guide...' or 'Our database shows this is commonly caused by...'"
            ]
        )
        
        self.prompt_add_section(
            "Resolution & Follow-up",
            body="End support interactions properly:",
            bullets=[
                "Summarize what was done and what fixed the issue",
                "Provide preventive tips to avoid future problems",
                "Offer to create a ticket for follow-up if needed",
                "Ask if there's anything else they need help with",
                "Thank them for their patience"
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
