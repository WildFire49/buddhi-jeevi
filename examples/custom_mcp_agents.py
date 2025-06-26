#!/usr/bin/env python3
"""
Example showing how to create and integrate custom MCP agents.
This demonstrates the modular architecture for easy agent extension.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_agent import BaseMCPAgent, MCPAgentFactory
from request_handler.mcp_agent_handler import MCPAgentHandler
from typing import List

class CustomerServiceMCPAgent(BaseMCPAgent):
    """Custom MCP agent for customer service and support queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("customer_service_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate customer service queries."""
        return [
            "customer", "support", "complaint", "issue", "problem", "help",
            "ticket", "escalation", "resolution", "feedback", "satisfaction",
            "service", "contact", "call center", "chat support"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a customer service query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        return keyword_count >= 1

class ComplianceMCPAgent(BaseMCPAgent):
    """Custom MCP agent for compliance and regulatory queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("compliance_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate compliance queries."""
        return [
            "compliance", "regulatory", "audit", "policy", "procedure", "guideline",
            "rbi", "sebi", "nbfc", "kyc", "aml", "cibil", "credit bureau",
            "documentation", "verification", "legal", "risk", "governance"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a compliance query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        return keyword_count >= 1

class RiskManagementMCPAgent(BaseMCPAgent):
    """Custom MCP agent for risk management and assessment queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("risk_management_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate risk management queries."""
        return [
            "risk", "assessment", "score", "rating", "default", "probability",
            "exposure", "mitigation", "portfolio", "concentration", "diversification",
            "stress test", "scenario", "monte carlo", "var", "expected loss"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a risk management query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        return keyword_count >= 1

def demonstrate_custom_agents():
    """Demonstrate how to add custom agents to the system."""
    
    print("=== MCP Agent Modularity Demo ===\n")
    
    # Method 1: Using MCPAgentHandler (recommended for production)
    print("1. Creating MCP Agent Handler with default agents:")
    handler = MCPAgentHandler()
    print(f"   Default agents: {handler.list_available_agents()}")
    
    # Add custom agents
    print("\n2. Adding custom agents:")
    handler.add_custom_agent(CustomerServiceMCPAgent())
    handler.add_custom_agent(ComplianceMCPAgent())
    handler.add_custom_agent(RiskManagementMCPAgent())
    
    print(f"   All agents now: {handler.list_available_agents()}")
    
    # Method 2: Using MCPAgentFactory directly (for advanced use cases)
    print("\n3. Using MCPAgentFactory directly:")
    factory = MCPAgentFactory()
    factory.add_agent(CustomerServiceMCPAgent())
    
    print(f"   Factory agents: {[agent.agent_name for agent in factory.get_all_agents()]}")
    
    # Test query routing
    print("\n4. Testing query routing:")
    test_queries = [
        "What is the collection performance for this month?",  # Dashboard
        "I need help with a customer complaint",              # Customer Service
        "What are the RBI compliance requirements?",          # Compliance
        "Calculate the risk score for this portfolio",        # Risk Management
        "Generate a monthly report",                          # Reporting
        "Predict loan defaults using ML",                     # Analytics
        "How do I complete KYC verification?"                 # Workflow (no agent)
    ]
    
    for query in test_queries:
        selected_agent = factory.get_agent_for_query(query)
        agent_name = selected_agent.agent_name if selected_agent else "No agent (workflow)"
        print(f"   '{query[:50]}...' -> {agent_name}")

if __name__ == "__main__":
    demonstrate_custom_agents()
