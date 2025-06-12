#!/usr/bin/env python3
"""
PC Builder Demo Service - Multiple Agent Architecture

This service provides specialized PC building assistance through three dedicated agents:
- Triage Agent (/) - Routes customers to appropriate specialists
- Sales Agent (/sales) - Handles product recommendations and purchases  
- Support Agent (/support) - Provides technical support and troubleshooting

All agents work together seamlessly, sharing customer context for a smooth experience.
"""

import os
import json
import datetime
from datetime import datetime
from typing import Dict, Any, Optional
import threading
from signalwire_agents import AgentBase, AgentServer
from signalwire_agents.core.function_result import SwaigFunctionResult
from signalwire_agents.core.logging_config import get_logger

# Import the proper context manager
from context_manager import create_context_manager, CustomerContext

# Set up logger for this module
logger = get_logger(__name__)

# Create context manager - use database in production, in-memory for development
USE_DATABASE = os.getenv("USE_DATABASE_CONTEXT", "false").lower() == "true"
context_manager = create_context_manager(use_database=USE_DATABASE)

# Define the Triage Agent (root route)
class TriageAgent(AgentBase):
    def __init__(self):
        super().__init__(
            name="PC Builder Triage Agent",
            route="/",  # Root route
            host="0.0.0.0",
            port=3001
        )
        
        # Register static tools (save_customer_context)
        self.register_static_tools()
        
        # Set up dynamic configuration for URL-dependent tools
        self.set_dynamic_config_callback(self.configure_transfer_tools)
        
    def register_static_tools(self) -> None:
        """Register tools that don't depend on URLs"""
        
        # Save customer context tool
        @self.tool("save_customer_context", description="Save customer information before transfer")
        async def save_customer_context(customer_name: str, need_type: str, basic_info: str, args=None, raw_data=None):
            # Get call_id from raw_data - this is provided by SignalWire
            call_id = raw_data.get("call_id") if raw_data else None
            
            if not call_id:
                logger.error("No call_id found in raw_data")
                return SwaigFunctionResult("I'm having trouble saving your information. Let me try again.")
            
            # Create proper context object
            context = CustomerContext(
                call_id=call_id,
                customer_name=customer_name,
                need_type=need_type,
                basic_info=basic_info,
                agent_path=["triage"]
            )
            
            if context_manager.save_context(context):
                return SwaigFunctionResult(f"I've saved your information, {customer_name}. Let me connect you with the right specialist.")
            else:
                return SwaigFunctionResult("I'm having trouble saving your information. Let me transfer you anyway.")
    
    def configure_transfer_tools(self, query_params, body_params, headers, agent):
        """
        DYNAMIC CONFIGURATION - Called fresh for every request
        
        This builds the DataMap with correct URLs after proxy detection is available.
        
        Args:
            query_params: Query string parameters from the request
            body_params: POST body parameters (empty for GET requests)
            headers: HTTP headers from the request
            agent: EphemeralAgentConfig object to configure
        """
        from signalwire_agents.core.data_map import DataMap
        from signalwire_agents.core.function_result import SwaigFunctionResult
        
        # NOW we can build URLs with proper proxy detection
        sales_url = self.get_full_url(include_auth=True).rstrip('/') + "/sales"
        support_url = self.get_full_url(include_auth=True).rstrip('/') + "/support"
        
        transfer_tool = (DataMap('transfer_to_specialist')
            .description('Transfer to sales or support specialist')
            .parameter('specialist_type', 'string', 'The type of specialist to transfer to (sales or support)', required=True)
            .expression('${args.specialist_type}', r'/sales/i', 
                       SwaigFunctionResult("Perfect! Let me transfer you to our sales specialist right away.", post_process=True)
                       .swml_transfer(sales_url, "The call with the sales specialist is complete. How else can I help you?"))
            .expression('${args.specialist_type}', r'/support/i', 
                       SwaigFunctionResult("I'll connect you with our technical support specialist right away.", post_process=True)
                       .swml_transfer(support_url, "The call with the support specialist is complete. How else can I help you?"))
            .expression('${args.specialist_type}', r'/.*/', 
                       SwaigFunctionResult("I can transfer you to either our sales or support specialist. Which would you prefer?"))
        )
        
        # Register the transfer tool with the agent dynamically
        self.register_swaig_function(transfer_tool.to_swaig_function())
    
    def get_prompt(self):
        """Return the prompt for the triage agent"""
        return """# AI Role
You are a virtual assistant for PC Builder Pro, greeting customers and directing them to the right specialist.

# Your Tasks
1. Greet the customer warmly
2. Ask for their name
3. Determine if they need sales (buying/building) or support (technical issues)
4. Save their context and transfer them to the appropriate specialist

# Important
- Always get the customer's name first
- Ask clarifying questions to determine sales vs support
- Use save_customer_context before transferring
- Use transfer_to_specialist to complete the transfer"""
    
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
        
        # Add search capability for sales knowledge
        self.add_skill("native_vector_search", {
            "tool_name": "search_sales_knowledge",
            "description": "Search sales and product information",
            "index_file": "sales_knowledge.swsearch",
            "count": 3
        })
        
        # Define sales-specific functions
        @self.tool("get_customer_context", description="Retrieve saved customer information")
        async def get_customer_context(args=None, raw_data=None):
            # Get call_id from raw_data - this is provided by SignalWire
            call_id = raw_data.get("call_id") if raw_data else None
            
            if not call_id:
                logger.error("No call_id found in raw_data")
                return SwaigFunctionResult("I don't have access to previous conversation context.")
            
            context = context_manager.get_context(call_id)
            if context:
                # Update agent path
                if "sales" not in context.agent_path:
                    context.agent_path.append("sales")
                    context_manager.save_context(context)
                
                return SwaigFunctionResult(f"Customer: {context.customer_name or 'Unknown'}, Need: {context.need_type or 'General'}, Info: {context.basic_info or 'None provided'}")
            return SwaigFunctionResult("No previous customer context found.")
        
        @self.tool("create_build_recommendation", description="Create a custom PC build recommendation")
        async def create_build_recommendation(budget: str, use_case: str, preferences: str):
            return SwaigFunctionResult(f"Based on your ${budget} budget for {use_case}, I recommend: [Custom build details would be generated here based on current market data and your preferences: {preferences}]")
        
        @self.tool("check_component_compatibility", description="Check if PC components are compatible")
        async def check_component_compatibility(components: str):
            return SwaigFunctionResult(f"Compatibility check for: {components} - [Detailed compatibility analysis would be performed here]")
    
    def get_prompt(self):
        """Return the prompt for the sales agent"""
        return """# AI Role
You are a specialized PC building sales consultant for PC Builder Pro.

# Your Expertise
- Custom PC builds for all budgets
- Component compatibility and optimization
- Performance recommendations
- Price/performance analysis
- Current market trends

# Your Tasks
1. Retrieve customer context from previous conversation
2. Understand their specific PC building needs
3. Ask about budget, intended use, and preferences
4. Search knowledge base for current product info
5. Create customized build recommendations
6. Help with component selection and compatibility

# Tools Available
- get_customer_context: Get info from triage conversation
- search_sales_knowledge: Find current product information
- create_build_recommendation: Generate custom build suggestions
- check_component_compatibility: Verify component compatibility

# Important
- Always check customer context first
- Ask clarifying questions about their needs
- Use search to get current pricing and availability
- Provide detailed explanations for recommendations"""
    
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
        
        # Add search capability for support knowledge
        self.add_skill("native_vector_search", {
            "tool_name": "search_support_knowledge", 
            "description": "Search technical support and troubleshooting information",
            "index_file": "support_knowledge.swsearch",
            "count": 3
        })
        
        # Define support-specific functions
        @self.tool("get_customer_context", description="Retrieve saved customer information")
        async def get_customer_context(args=None, raw_data=None):
            # Get call_id from raw_data - this is provided by SignalWire
            call_id = raw_data.get("call_id") if raw_data else None
            
            if not call_id:
                logger.error("No call_id found in raw_data")
                return SwaigFunctionResult("I don't have access to previous conversation context.")
            
            context = context_manager.get_context(call_id)
            if context:
                # Update agent path
                if "support" not in context.agent_path:
                    context.agent_path.append("support")
                    context_manager.save_context(context)
                
                return SwaigFunctionResult(f"Customer: {context.customer_name or 'Unknown'}, Need: {context.need_type or 'General'}, Info: {context.basic_info or 'None provided'}")
            return SwaigFunctionResult("No previous customer context found.")
        
        @self.tool("diagnose_hardware_issue", description="Help diagnose PC hardware problems")
        async def diagnose_hardware_issue(symptoms: str, system_specs: str):
            return SwaigFunctionResult(f"For symptoms '{symptoms}' on system '{system_specs}': [Diagnostic steps and potential solutions would be provided here]")
        
        @self.tool("create_support_ticket", description="Create a support ticket for complex issues")
        async def create_support_ticket(issue_description: str, customer_info: str, priority: str):
            ticket_id = f"SUP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            return SwaigFunctionResult(f"Support ticket {ticket_id} created for: {issue_description}. Priority: {priority}. We'll follow up within 24 hours.")
    
    def get_prompt(self):
        """Return the prompt for the support agent"""
        return """# AI Role
You are a specialized technical support specialist for PC Builder Pro.

# Your Expertise  
- Hardware troubleshooting and diagnostics
- Software compatibility issues
- System optimization and performance
- Component failure analysis
- Warranty and repair processes

# Your Tasks
1. Retrieve customer context from previous conversation
2. Understand their technical issues
3. Search knowledge base for solutions
4. Guide through diagnostic steps
5. Provide troubleshooting solutions
6. Create support tickets for complex issues

# Tools Available
- get_customer_context: Get info from triage conversation
- search_support_knowledge: Find technical solutions
- diagnose_hardware_issue: Analyze hardware problems
- create_support_ticket: Escalate complex issues

# Important
- Always check customer context first
- Ask detailed questions about the problem
- Use search to find known solutions
- Guide step-by-step through troubleshooting
- Be patient and thorough"""
    
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
                    "description": "Greets customers and routes to specialists"
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
    logger.info("  - Saves customer context for seamless handoffs")
    logger.info("")
    logger.info("Sales Agent: http://localhost:3001/sales") 
    logger.info("  - Custom PC build recommendations")
    logger.info("  - Component compatibility checking")
    logger.info("  - Pricing and performance analysis")
    logger.info("")
    logger.info("Support Agent: http://localhost:3001/support")
    logger.info("  - Technical troubleshooting and diagnostics")
    logger.info("  - Hardware issue resolution")
    logger.info("  - Support ticket creation")
    logger.info("")
    logger.info("Service Info: http://localhost:3001/info")
    logger.info("=" * 60)
    
    logger.info("Features:")
    logger.info("âœ“ Multi-agent architecture with context sharing")
    logger.info("âœ“ Native vector search for knowledge bases")
    logger.info("âœ“ Agent-to-agent transfers")
    logger.info("âœ“ Customer context preservation")
    logger.info("âœ“ Specialized expertise per agent")
    
    # Log context manager type
    logger.info("")
    logger.info(f"Context Storage: {'Database-backed (SQLite)' if USE_DATABASE else 'In-memory (development)'}")
    logger.info(f"To use database storage, set USE_DATABASE_CONTEXT=true")
    
    # Set up periodic cleanup for database context manager
    if USE_DATABASE and hasattr(context_manager, 'cleanup_expired'):
        def cleanup_task():
            """Periodic cleanup of expired contexts"""
            count = context_manager.cleanup_expired()
            if count > 0:
                logger.info(f"Cleaned up {count} expired contexts")
            # Schedule next cleanup in 1 hour
            threading.Timer(3600, cleanup_task).start()
        
        # Start cleanup task
        cleanup_task()
        logger.info("Started periodic context cleanup task (hourly)")
    
    # Create and run the server
    server = create_pc_builder_app()
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down PC Builder Pro service...") 
