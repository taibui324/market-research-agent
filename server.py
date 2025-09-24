# server.py
from fastmcp import FastMCP

mcp = FastMCP("hello-mcp")


@mcp.tool()
def echo(text: str) -> str:
    """Echo a string back to the caller."""
    return text


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b

@mcp.tool()
def tellJoke(topic: str) -> str:
    """Tell a joke."""
    return "Tell a joke about " + topic

@mcp.tool()
def generate_pdf(text: str) -> str:
    """Generate a PDF from text."""
    return "Generating PDF..."

if __name__ == "__main__":
    # Runs an MCP server over stdio (default), perfect for local testing or editors.
    mcp.run()
