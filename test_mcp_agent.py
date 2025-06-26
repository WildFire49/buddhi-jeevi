#!/usr/bin/env python3
"""
Test script for modular MCP agent integration.
This script tests both direct MCP agent queries and chat-based routing with multiple agents.
"""

import requests
import json
import time
from typing import Dict, Any

# Server configuration
SERVER_URL = "http://localhost:8002"  # Update with your server URL if different
TEST_SESSION_ID = "test-session-mcp-integration"

def test_direct_mcp_query(question: str) -> Dict[str, Any]:
    """Test the direct MCP dashboard query endpoint."""
    print(f"\n--- Testing Direct MCP Query: '{question}' ---")
    
    url = f"{SERVER_URL}/mcp-dashboard-query"
    payload = {
        "question": question,
        "session_id": TEST_SESSION_ID
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Agent: {result.get('agent_name', 'unknown')}")
        print(f"Message: {result.get('message', 'No message')}")
        
        if 'data' in result and result['data']:
            print("Data received:")
            print(json.dumps(result['data'], indent=2))
        else:
            print("No data returned or empty data")
            
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}

def test_chat_routing(prompt: str) -> Dict[str, Any]:
    """Test the chat endpoint with routing logic."""
    print(f"\n--- Testing Chat Routing: '{prompt}' ---")
    
    url = f"{SERVER_URL}/chat"
    payload = {
        "prompt": prompt,
        "session_id": TEST_SESSION_ID
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("Response received:")
        if isinstance(result.get("response"), dict) and "dashboard_data" in result.get("response", {}):
            print("Dashboard data detected in response")
            response_data = result.get("response", {})
            print(f"Source: {response_data.get('source', 'unknown')}")
            print(json.dumps(response_data.get("dashboard_data", {}), indent=2))
        else:
            print(f"Regular workflow response: {str(result.get('response', 'No response'))[:200]}...")
            
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("=== TESTING MODULAR MCP AGENT INTEGRATION ===")
    
    # Test direct MCP queries for different agent types
    print("\n=== TESTING DIRECT MCP QUERIES ===")
    
    # Dashboard/metrics queries
    test_direct_mcp_query("What is the collection performance for Kumbakonam CEC this month?")
    time.sleep(1)
    
    test_direct_mcp_query("Show me disbursement details for Tamil Nadu region in the past quarter")
    time.sleep(1)
    
    # Analytics queries
    test_direct_mcp_query("Predict loan default trends using machine learning models")
    time.sleep(1)
    
    # Reporting queries
    test_direct_mcp_query("Generate a monthly compliance report for our portfolio")
    time.sleep(1)
    
    # Test chat routing with various query types
    print("\n=== TESTING CHAT-BASED ROUTING ===")
    
    # Workflow query (should NOT route to MCP)
    test_chat_routing("How do I verify customer identity for KYC?")
    time.sleep(1)
    
    # Dashboard query (should route to dashboard agent)
    test_chat_routing("for this month collection how much collected so far and how much its pending in kumbakonam cec?")
    time.sleep(1)
    
    # Analytics query (should route to analytics agent)
    test_chat_routing("Can you analyze the correlation between loan amounts and default rates?")
    time.sleep(1)
    
    # Reporting query (should route to reporting agent)
    test_chat_routing("I need to export a CSV report of all disbursements this quarter")
    time.sleep(1)
    
    # Mixed intent query
    test_chat_routing("After completing prospect info collection, show me the portfolio performance metrics")
    time.sleep(1)
    
    # Edge case - ambiguous query
    test_chat_routing("What should I do next?")
    
    print("\n=== ALL TESTS COMPLETED ===")
    print("\nExpected Results:")
    print("- Dashboard queries should route to 'dashboard_agent'")
    print("- Analytics queries should route to 'analytics_agent'") 
    print("- Reporting queries should route to 'reporting_agent'")
    print("- Workflow queries should use normal RAG processing")
    print("- Mixed queries should route to the most relevant agent")
