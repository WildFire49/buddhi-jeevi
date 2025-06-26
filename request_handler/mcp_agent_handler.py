import json
import logging
from typing import Dict, Any, List, Optional

from mcp_agent import MCPAgentFactory, BaseMCPAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPAgentHandler:
    """Handler for determining whether to route queries to MCP agents and processing agent responses."""
    
    def __init__(self, mcp_agent_url: Optional[str] = None):
        """Initialize the MCP agent handler with a factory for managing multiple agents.
        
        Args:
            mcp_agent_url: Optional URL for the MCP agents. If not provided, defaults will be used.
        """
        self.agent_factory = MCPAgentFactory(base_url=mcp_agent_url)
        logger.info(f"Initialized MCP Agent Handler with {len(self.agent_factory.get_all_agents())} agents")
    
    def add_custom_agent(self, agent: BaseMCPAgent):
        """Add a custom MCP agent to the handler.
        
        Args:
            agent: Instance of a BaseMCPAgent subclass
        """
        self.agent_factory.add_agent(agent)
        logger.info(f"Added custom agent: {agent.agent_name}")
    
    def process_query(self, query: str, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query by deciding whether to route to an MCP agent and handling the response.
        
        Args:
            query: The user's query text
            session_id: Session ID for the request
            metadata: Optional metadata to pass to the MCP agent (overrides default metadata)
        
        Returns:
            Dict with processed response that can be returned to the client
        """
        # Find the most appropriate agent for this query
        selected_agent = self.agent_factory.get_agent_for_query(query)
        
        if selected_agent:
            logger.info(f"Routing query to {selected_agent.agent_name}: {query}")
            
            # Query the selected MCP agent with optional metadata
            mcp_response = selected_agent.query_agent(query, session_id, metadata)
            
            # Transform the response into the format expected by the client
            return self._format_mcp_response(mcp_response, selected_agent.agent_name)
        else:
            logger.info(f"Query not routed to any MCP agent: {query}")
            return {
                "routed_to_mcp": False,
                "message": "Query not related to any available MCP agent capabilities"
            }
    
    def should_route_to_mcp_agent(self, query: str) -> bool:
        """Determine if a query should be routed to any MCP agent.
        
        Args:
            query: The user's query
            
        Returns:
            Boolean indicating if the query should be routed to an MCP agent
        """
        # Check if any agent can handle this query
        selected_agent = self.agent_factory.get_agent_for_query(query)
        return selected_agent is not None
    
    def get_agent_by_name(self, agent_name: str) -> Optional[BaseMCPAgent]:
        """Get a specific agent by name for direct access.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            The agent instance or None if not found
        """
        return self.agent_factory.get_agent_by_name(agent_name)
    
    def list_available_agents(self) -> List[str]:
        """Get a list of all available agent names.
        
        Returns:
            List of agent names
        """
        return [agent.agent_name for agent in self.agent_factory.get_all_agents()]
    
    def _format_mcp_response(self, mcp_response: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Format the MCP agent response into the structure expected by the client.
        
        Args:
            mcp_response: The raw response from the MCP agent
            agent_name: Name of the agent that processed the query
            
        Returns:
            Dict with formatted response
        """
        try:
            # Check if there was an error in the MCP response
            if "error" in mcp_response:
                return {
                    "routed_to_mcp": True,
                    "agent_name": agent_name,
                    "status": "error",
                    "message": mcp_response.get("message", f"Error retrieving data from {agent_name}"),
                    "data": {},
                    "error": mcp_response.get("error")
                }
            
            # Extract the results from the MCP response
            # The structure may vary depending on your MCP agent's response format
            result = mcp_response.get("result", {})
            
            return {
                "routed_to_mcp": True,
                "agent_name": agent_name,
                "status": "success",
                "message": f"Data retrieved from {agent_name}",
                "data": result
            }
        except Exception as e:
            logger.error(f"Error formatting MCP response from {agent_name}: {e}")
            return {
                "routed_to_mcp": True,
                "agent_name": agent_name,
                "status": "error",
                "message": f"Error processing {agent_name} response: {str(e)}",
                "data": {},
                "error": str(e)
            }
