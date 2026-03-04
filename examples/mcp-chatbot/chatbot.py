#!/usr/bin/env python3
"""
Llama Stack Chatbot with MCP Tools (Kubernetes + ArgoCD)

Uses the Responses API which handles tool execution internally.
No manual iteration loop needed - the API executes tools and generates
the final response in a single call.

Unlike rag-mcp-chatbot, this example does NOT use RAG/file_search.
It relies solely on MCP tools to diagnose application issues.

NOTE: The ArgoCD MCP server (argoproj-labs/mcp-for-argocd) in SSE mode
reads credentials from HTTP headers, not environment variables. This
chatbot passes the required headers (x-argocd-base-url, x-argocd-api-token)
via the Llama Stack Responses API tool configuration. Set ARGOCD_BASE_URL
and ARGOCD_API_TOKEN in your environment or .env file.
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

        self.instructions = """You are a DevOps/Kubernetes specialist. You have ArgoCD and Kubernetes tools.

RULES:
- Call the tools you need, then provide a FINAL TEXT ANSWER with your diagnosis.
- After calling tools, do NOT suggest more tool calls. Summarize what you found.
- ArgoCD application names may differ from the service name (e.g. "app-discounts-helm" for "discounts").
- Use list_applications first to find exact names, then get_application for details.
- Provide specific details: sync status, health status, error messages, pod states."""

    def _setup_client(self):
        skip_ssl = os.getenv("SKIP_SSL_VERIFY", "False").lower() == "true"
        timeout = int(os.getenv("LLAMA_STACK_TIMEOUT", "300"))

        http_client = httpx.Client(verify=not skip_ssl, timeout=timeout)
        self.client = LlamaStackClient(
            base_url=self.base_url,
            http_client=http_client
        )
        print(f"Connected to: {self.base_url}")

    def _get_argocd_headers(self):
        """Build headers for the ArgoCD MCP server (SSE transport requires them)."""
        base_url = os.getenv("ARGOCD_BASE_URL", "")
        api_token = os.getenv("ARGOCD_API_TOKEN", "")
        if base_url and api_token:
            return {
                "x-argocd-base-url": base_url,
                "x-argocd-api-token": api_token,
            }
        return None

    def _setup_mcp_tools(self):
        """Discover and register all mcp::* toolgroups dynamically."""
        print("Checking MCP toolgroups...")

        argocd_headers = self._get_argocd_headers()
        if argocd_headers:
            print("  ArgoCD credentials: loaded from environment")
        else:
            print("  WARNING: ARGOCD_BASE_URL/ARGOCD_API_TOKEN not set; ArgoCD tools may fail")

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
                    tools = list(self.client.tools.list(toolgroup_id=tg.identifier))
                    tool_names = [getattr(t, 'name', str(t)) for t in tools]
                    tool_config = {
                        "type": "mcp",
                        "server_label": label,
                        "server_url": mcp_url,
                    }
                    if label == "argocd" and argocd_headers:
                        tool_config["headers"] = argocd_headers
                    self.tools.append(tool_config)
                    preview = ', '.join(tool_names[:5])
                    if len(tool_names) > 5:
                        preview += '...'
                    print(f"  {tg.identifier}: {len(tool_names)} tools ({preview})")
                except Exception as e:
                    print(f"  {tg.identifier}: unreachable at {mcp_url}, skipping ({e})")

        except Exception as e:
            print(f"MCP setup error: {e}")

    def chat(self, message: str):
        """Send a message and get a response with automatic MCP tool execution."""
        try:
            print(f"\nProcessing: '{message}'")
            print(f"Tools: {len(self.tools)}")
            print("=" * 60)

            resp = self.client.responses.create(
                model=self.model_id,
                input=message,
                instructions=self.instructions,
                tools=self.tools if self.tools else None,
                max_infer_iters=int(os.getenv("MAX_INFER_ITERS", "3")),
                stream=False,
            )

            tool_calls = []
            for item in resp.output:
                d = item.model_dump() if hasattr(item, 'model_dump') else {}
                item_type = d.get('type', '')
                if item_type == 'mcp_call':
                    name = d.get('name', 'mcp_tool')
                    error = d.get('error')
                    output = d.get('output', '')
                    status = 'error' if error else 'ok'
                    tool_calls.append({"tool": name, "status": status, "result": output or str(error)})

            ok_calls = [tc for tc in tool_calls if tc['status'] == 'ok']
            failed_calls = [tc for tc in tool_calls if tc['status'] != 'ok']

            print("\n" + "=" * 60)
            print(f"Tool calls: {len(tool_calls)} ({len(ok_calls)} ok, {len(failed_calls)} failed)")
            for i, tc in enumerate(ok_calls[:10]):
                preview = str(tc['result'])[:80]
                if len(str(tc['result'])) > 80:
                    preview += "..."
                print(f"   {i+1}. {tc['tool']}: {preview}")
            for tc in failed_calls[:5]:
                print(f"   FAILED: {tc['tool']}: {str(tc['result'])[:100]}")

            output_text = resp.output_text or "(no text response)"
            print(f"\nResponse:\n{output_text}")

            return resp

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    chatbot = MCPChatbot()

    query = os.getenv("TEST_QUERY",
        "What is the status of the discounts application? "
        "Check ArgoCD (app name may be app-discounts-helm) and the Kubernetes pods "
        "in the llama-stack-example namespace. Give me a diagnosis.")

    print(f"\nQuery: {query}")
    chatbot.chat(query)


if __name__ == "__main__":
    main()
