import json
import logging
import os
import requests
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseMCPAgent(ABC):
    """Base class for MCP agents. All specific agents should inherit from this."""
    
    def __init__(self, agent_name: str, base_url: str = None):
        """Initialize the base MCP agent.
        
        Args:
            agent_name: Name of the specific agent (e.g., 'dashboard_agent', 'analytics_agent')
            base_url: Base URL for the MCP agent. Defaults to localhost:8000 if not specified.
        """
        self.agent_name = agent_name
        self.base_url = base_url or os.getenv("MCP_AGENT_URL", "http://localhost:8000")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        logger.info(f"Initialized {self.agent_name} MCP Agent with base URL: {self.base_url}")
    
    @abstractmethod
    def should_handle_query(self, query: str) -> bool:
        """Determine if this agent should handle the given query.
        
        Args:
            query: The user's query
            
        Returns:
            Boolean indicating if this agent should handle the query
        """
        pass
    
    @abstractmethod
    def get_agent_keywords(self) -> List[str]:
        """Get the keywords that this agent handles.
        
        Returns:
            List of keywords relevant to this agent
        """
        pass
    
    def get_default_metadata(self) -> Dict[str, Any]:
        """
        Get the default metadata for this agent. Override in subclasses to provide custom metadata.
        
        Returns:
            Dict with default metadata (empty by default)
        """
        return {}
    
    def query_agent(self, question: str, session_id: str = "default-session", metadata: Optional[Dict[str, Any]] = None) -> Dict[Any, Any]:
        """
        Query the MCP agent with a specific question.
        
        Args:
            question: The query to send to the MCP agent
            session_id: Session ID for the request
            metadata: Optional metadata to include in the request (overrides default metadata)
            
        Returns:
            Dict with the MCP agent response
        """
        url = f"{self.base_url}/mcp"
        
        headers = self.headers.copy()
        headers["X-Session-ID"] = session_id
        
        # Get agent-specific default metadata if none provided
        agent_metadata = metadata if metadata is not None else self.get_default_metadata()
        
        # Build the arguments structure with metadata
        arguments = {
            "question": question
        }
        
        # Add metadata only if not empty
        if agent_metadata:
            arguments["metadata"] = agent_metadata
        
        payload = {
            "method": "tools/call",
            "params": {
                "name": self.agent_name,
                "arguments": arguments
            }
        }
        
        try:
            logger.info(f"Sending request to {self.agent_name}: {question}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            logger.info(f"Received {self.agent_name} response: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying {self.agent_name}: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "message": f"Failed to retrieve data from {self.agent_name}"
            }

class DashboardMCPAgent(BaseMCPAgent):
    """MCP agent for dashboard and statistical data queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("dashboard_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate dashboard/statistics queries."""
        return [
            "collections", "disbursement", "region", "state", "cec", "fo", "vo", 
            "metrics", "dashboard", "statistics", "performance", "pending",
            "collected", "amount", "loan", "this month", "last month", "year",
            "percentage", "total", "average", "portfolio", "overdue", "late payment",
            "analytics", "report", "summary", "trends"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a dashboard/statistics query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        # If at least 2 dashboard keywords are present, consider it a dashboard query
        return keyword_count >= 2

class AnalyticsMCPAgent(BaseMCPAgent):
    """MCP agent for advanced analytics and data science queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("analytics_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate analytics queries."""
        return [
            "predict", "forecast", "trend", "analysis", "correlation", "regression",
            "machine learning", "ai", "model", "algorithm", "pattern", "insight",
            "behavior", "segmentation", "clustering", "classification", "anomaly"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is an analytics query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Analytics queries might have fewer but more specific keywords
        return keyword_count >= 1

class ReportingMCPAgent(BaseMCPAgent):
    """MCP agent for reporting and document generation queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("reporting_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate reporting queries."""
        return [
            "report", "generate", "export", "document", "pdf", "excel", "csv",
            "summary", "statement", "compliance", "audit", "regulatory", "monthly report",
            "quarterly report", "annual report", "financial statement"
        ]
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a reporting query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        return keyword_count >= 1

class CreditMCPAgent(BaseMCPAgent):
    """MCP agent for credit scoring and loan decision queries."""
    
    def __init__(self, base_url: str = None):
        super().__init__("credit_agent", base_url)
    
    def get_agent_keywords(self) -> List[str]:
        """Get keywords that indicate credit scoring queries."""
        return [
            "credit score", "loan decision", "approval", "reject", "interest rate", 
            "risk assessment", "borrower", "credit history", "credit limit", 
            "credit check", "eligibility", "underwriting", "loan application",
            "credit evaluation", "loan processing", "borrower profile"
        ]
    
    def get_default_metadata(self) -> Dict[str, Any]:
        """Override to provide default metadata for the credit agent."""
        return {
            "creditScoringModel": "v2.1",
            "underwritingVersion": "3.0",
            "includeHistoricalData": True,
            "riskAssessmentLevel": "detailed"
        }
    
    def should_handle_query(self, query: str) -> bool:
        """Determine if this is a credit scoring query."""
        query_lower = query.lower()
        keywords = self.get_agent_keywords()
        keyword_count = sum(1 for keyword in keywords if keyword in query_lower)
        
        return keyword_count >= 1


class MCPAgentFactory:
    """Factory class for creating and managing MCP agents."""
    
    def __init__(self, base_url: str = None):
        """Initialize the factory with available agents.
        
        Args:
            base_url: Base URL for all MCP agents
        """
        self.base_url = base_url
        self.agents: List[BaseMCPAgent] = []
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize the default set of MCP agents."""
        self.agents = [
            DashboardMCPAgent(self.base_url),
            AnalyticsMCPAgent(self.base_url),
            ReportingMCPAgent(self.base_url),
            CreditMCPAgent(self.base_url)
        ]
        logger.info(f"Initialized {len(self.agents)} MCP agents")
    
    def add_agent(self, agent: BaseMCPAgent):
        """Add a custom agent to the factory.
        
        Args:
            agent: Instance of a BaseMCPAgent subclass
        """
        self.agents.append(agent)
        logger.info(f"Added custom agent: {agent.agent_name}")
    
    def get_agent_for_query(self, query: str) -> Optional[BaseMCPAgent]:
        """Get the most appropriate agent for a given query.
        
        Args:
            query: The user's query
            
        Returns:
            The best matching agent or None if no agent should handle the query
        """
        # Check each agent to see if it should handle the query
        for agent in self.agents:
            if agent.should_handle_query(query):
                logger.info(f"Selected agent {agent.agent_name} for query: {query}")
                return agent
        
        logger.info(f"No agent selected for query: {query}")
        return None
    
    def get_all_agents(self) -> List[BaseMCPAgent]:
        """Get all registered agents."""
        return self.agents.copy()
    
    def get_agent_by_name(self, agent_name: str) -> Optional[BaseMCPAgent]:
        """Get a specific agent by name.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            The agent instance or None if not found
        """
        for agent in self.agents:
            if agent.agent_name == agent_name:
                return agent
        return None
