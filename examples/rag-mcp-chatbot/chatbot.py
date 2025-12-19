#!/usr/bin/env python3
"""
Llama Stack Chatbot with RAG + MCP Tools

Uses the Responses API which handles tool execution internally.
No manual iteration loop needed - the API executes tools and generates
the final response in a single call.
"""

import os
import httpx
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()


class LlamaStackChatbot:
    def __init__(self):
        self.base_url = os.getenv("REMOTE_BASE_URL", "http://localhost:8321")
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "granite32-8b")
        self.vector_store_id = os.getenv("VECTOR_STORE_ID")
        
        # Setup client
        self._setup_client()
        
        # Build tools list
        self.tools = []
        self._setup_mcp_tools()
        self._setup_rag_tools()
        
        print(f"📋 Tools configured: {len(self.tools)}")
        
        self.instructions = """You are a DevOps/Kubernetes specialist. Use the available tools to diagnose issues.

When troubleshooting:
1. Call pods_list with namespace parameter to check pod status
2. Call pods_log for any pod in CrashLoopBackOff or Error state
3. Search documentation for solutions

Execute ALL necessary tools before providing your final answer. Do not just describe what tools to call - actually call them."""

    
    def _setup_client(self):
        """Setup LlamaStackClient"""
        skip_ssl = os.getenv("SKIP_SSL_VERIFY", "False").lower() == "true"
        timeout = int(os.getenv("LLAMA_STACK_TIMEOUT", "300"))
        
        http_client = httpx.Client(verify=not skip_ssl, timeout=timeout)
        self.client = LlamaStackClient(
            base_url=self.base_url,
            http_client=http_client
        )
        print(f"✅ Connected to: {self.base_url}")
    
    def _setup_mcp_tools(self):
        """Setup MCP tools from registered toolgroups"""
        print("🔍 Checking MCP toolgroups...")
        
        try:
            toolgroups = {tg.identifier for tg in self.client.toolgroups.list()}
            
            if "mcp::openshift" in toolgroups:
                # Get MCP URL from registered toolgroup
                mcp_url = None
                for tg in self.client.toolgroups.list():
                    if tg.identifier == "mcp::openshift":
                        if hasattr(tg, 'mcp_endpoint') and tg.mcp_endpoint:
                            mcp_url = getattr(tg.mcp_endpoint, 'uri', '')
                            break
                
                if mcp_url:
                    self.tools.append({
                        "type": "mcp",
                        "server_label": "openshift",
                        "server_url": mcp_url
                    })
                    tools = self.client.tools.list(toolgroup_id="mcp::openshift")
                    print(f"✅ MCP OpenShift: {len(tools)} tools available")
                    
        except Exception as e:
            print(f"⚠️  MCP setup error: {e}")
    
    def _setup_rag_tools(self):
        """Setup RAG file_search tool"""
        if not self.vector_store_id:
            print("⚠️  No VECTOR_STORE_ID configured - RAG disabled")
            return
        
        self.tools.append({
            "type": "file_search",
            "vector_store_ids": [self.vector_store_id]
        })
        print(f"✅ RAG enabled with vector store: {self.vector_store_id}")
    
    def chat(self, message: str):
        """
        Send a message and get a response.
        
        The Responses API handles tool execution internally:
        1. LLM decides which tools to call
        2. Tools are executed automatically
        3. LLM generates final response with tool results
        
        All in a single API call - no manual loop needed.
        """
        try:
            print(f"\n🧠 Processing: '{message}'")
            print(f"🛠️  Tools: {len(self.tools)}")
            print("=" * 60)
            
            # Single call - API handles tool execution internally
            response = self.client.responses.create(
                model=self.model_id,
                input=message,
                instructions=self.instructions,
                tools=self.tools if self.tools else None,
                include=["file_search_call.results"],
                max_infer_iters=10,  # Allow multiple tool iterations
            )
            
            # Process and display results
            tool_results = []
            
            if hasattr(response, 'output') and isinstance(response.output, list):
                for item in response.output:
                    item_type = str(getattr(item, 'type', '')).lower()
                    
                    # MCP tool calls
                    if 'mcp' in item_type or hasattr(item, 'server_label'):
                        tool_name = getattr(item, 'name', 'mcp_tool')
                        print(f"   🔧 MCP: {tool_name}")
                        if hasattr(item, 'output'):
                            tool_results.append({"tool": tool_name, "result": item.output})
                    
                    # file_search calls
                    if hasattr(item, 'results') and isinstance(item.results, list):
                        print(f"   📄 RAG: {len(item.results)} documents retrieved")
                        for result in item.results:
                            if hasattr(result, 'text') and result.text:
                                tool_results.append({"tool": "file_search", "result": result.text})
            
            output_text = getattr(response, "output_text", None) or str(response)
            
            # Summary
            print("\n" + "="*60)
            print(f"📋 Tools executed: {len(tool_results)}")
            for i, tr in enumerate(tool_results[:5]):
                preview = str(tr['result'])[:60] + "..." if len(str(tr['result'])) > 60 else tr['result']
                print(f"   {i+1}. {tr['tool']}: {preview}")
            
            print(f"\n💬 Response:\n{output_text}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Run a test query"""
    chatbot = LlamaStackChatbot()
    
    query = os.getenv("TEST_QUERY", 
        "Why discounts application is not working in openshift-gitops namespace?")
    
    print(f"\n📝 Query: {query}")
    chatbot.chat(query)


if __name__ == "__main__":
    main()

