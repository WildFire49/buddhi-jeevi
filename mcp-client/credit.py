import asyncio
from fastmcp import Client as FastMCPClient
 
async def mail_router(mail_text: str) -> dict:
    """Connect to local MCP server and call a tool"""
    API_URL = "http://13.201.208.156:8200/mcp"

    async with FastMCPClient(API_URL, timeout=10000) as client:
        # 1. List tools
        tools = await client.list_tools()
        print("Available tools:", tools)
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
 
        if tools:
            tool_name = tools[0].name
            test_input = {"metadata": mail_text}
            result = await client.call_tool(tool_name, test_input)
            print(f"\n✅ Result from '{tool_name}':\n", result)
            return result
        else:
            print("❌ No tools available.")
            return {"error": "No tools found"}
 
# Run as script
if __name__ == "__main__":
    prompt = "Analyze this credit request."
    result = asyncio.run(mail_router(prompt))
    print("\n📦 Final output:\n", result)
 