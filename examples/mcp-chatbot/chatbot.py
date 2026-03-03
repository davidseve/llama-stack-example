#!/usr/bin/env python3
"""
Llama Stack Chatbot with MCP Tools (Kubernetes + ArgoCD)

Uses the Responses API which handles tool execution internally.
No manual iteration loop needed - the API executes tools and generates
the final response in a single call.

Unlike rag-mcp-chatbot, this example does NOT use RAG/file_search.
It relies solely on MCP tools to diagnose application issues.
"""

import os
import httpx
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()


class MCPChatbot:
    def __init__(self):
        self.base_url = os.getenv("REMOTE_BASE_URL", "http://localhost:8321")
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "granite32-8b")

        self._setup_client()

        self.tools = []
        self._setup_mcp_tools()

        print(f"Tools configured: {len(self.tools)}")

        self.instructions = """You are a DevOps/Kubernetes specialist with access to both Kubernetes and ArgoCD MCP tools.

When troubleshooting an application:
1. Use ArgoCD tools to check the application sync status, health, and any sync errors
2. Use Kubernetes tools to check pod status, logs, and events in the relevant namespace
3. Cross-reference ArgoCD desired state with actual Kubernetes state

Execute ALL necessary tools before providing your final answer. Do not just describe what tools to call - actually call them.
Provide a clear diagnosis with specific details from the tool outputs."""

    def _setup_client(self):
        skip_ssl = os.getenv("SKIP_SSL_VERIFY", "False").lower() == "true"
        timeout = int(os.getenv("LLAMA_STACK_TIMEOUT", "300"))

        http_client = httpx.Client(verify=not skip_ssl, timeout=timeout)
        self.client = LlamaStackClient(
            base_url=self.base_url,
            http_client=http_client
        )
        print(f"Connected to: {self.base_url}")

    def _setup_mcp_tools(self):
        """Discover and register all mcp::* toolgroups dynamically."""
        print("Checking MCP toolgroups...")

        try:
            all_toolgroups = list(self.client.toolgroups.list())
            mcp_toolgroups = [
                tg for tg in all_toolgroups
                if tg.identifier.startswith("mcp::")
            ]

            if not mcp_toolgroups:
                print("No MCP toolgroups registered in llama-stack")
                return

            for tg in mcp_toolgroups:
                label = tg.identifier.split("::", 1)[1]
                mcp_url = None
                if hasattr(tg, 'mcp_endpoint') and tg.mcp_endpoint:
                    mcp_url = getattr(tg.mcp_endpoint, 'uri', '')

                if not mcp_url:
                    print(f"  {tg.identifier}: no endpoint URI, skipping")
                    continue

                try:
                    tools = self.client.tools.list(toolgroup_id=tg.identifier)
                    tool_names = [t.identifier.split("::")[-1] for t in tools]
                    self.tools.append({
                        "type": "mcp",
                        "server_label": label,
                        "server_url": mcp_url
                    })
                    print(f"  {tg.identifier}: {len(tool_names)} tools ({', '.join(tool_names[:5])}{'...' if len(tool_names) > 5 else ''})")
                except Exception as e:
                    print(f"  {tg.identifier}: unreachable at {mcp_url}, skipping ({e})")

        except Exception as e:
            print(f"MCP setup error: {e}")

    def chat(self, message: str):
        """
        Send a message and get a response using streaming.

        Streaming keeps the connection alive with SSE events, which prevents
        the OpenShift route / HAProxy from timing out with a 504 during
        long-running tool executions.
        """
        try:
            print(f"\nProcessing: '{message}'")
            print(f"Tools: {len(self.tools)}")
            print("=" * 60)

            stream = self.client.responses.create(
                model=self.model_id,
                input=message,
                instructions=self.instructions,
                tools=self.tools if self.tools else None,
                max_infer_iters=10,
                stream=True,
            )

            tool_results = []
            output_text_parts = []
            final_response = None

            for event in stream:
                event_type = getattr(event, 'type', '')

                if event_type == 'response.completed':
                    final_response = getattr(event, 'response', None)
                    if final_response and hasattr(final_response, 'output'):
                        for item in final_response.output:
                            item_type = str(getattr(item, 'type', '')).lower()

                            if 'mcp' in item_type or hasattr(item, 'server_label'):
                                tool_name = getattr(item, 'name', 'mcp_tool')
                                print(f"   MCP: {tool_name}")
                                if hasattr(item, 'output'):
                                    tool_results.append({"tool": tool_name, "result": item.output})

                elif event_type == 'response.output_text.delta':
                    delta = getattr(event, 'delta', '')
                    if delta:
                        output_text_parts.append(delta)

                elif event_type == 'response.mcp_call.in_progress':
                    name = getattr(event, 'name', '')
                    print(f"   MCP calling: {name}...")

            if output_text_parts:
                output_text = ''.join(output_text_parts)
            elif final_response:
                output_text = getattr(final_response, 'output_text', None) or str(final_response)
            else:
                output_text = "(no response received)"

            print("\n" + "=" * 60)
            print(f"Tools executed: {len(tool_results)}")
            for i, tr in enumerate(tool_results[:10]):
                preview = str(tr['result'])[:80] + "..." if len(str(tr['result'])) > 80 else tr['result']
                print(f"   {i+1}. {tr['tool']}: {preview}")

            print(f"\nResponse:\n{output_text}")

            return final_response

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    chatbot = MCPChatbot()

    query = os.getenv("TEST_QUERY",
        "What is the status of the discounts application in the openshift-gitops namespace? "
        "Check both ArgoCD and the Kubernetes resources to diagnose any issues.")

    print(f"\nQuery: {query}")
    chatbot.chat(query)


if __name__ == "__main__":
    main()
