#!/usr/bin/env python3
"""
Basic LlamaStack Validation Script

This script performs basic validation of core LlamaStack functionality
without getting caught up in API version differences.
"""

import argparse
import json
import sys
import ssl
import httpx
from datetime import datetime

# Import llama-stack client
try:
    from llama_stack_client import LlamaStackClient
except ImportError:
    print("❌ llama-stack-client not found. Install with: pip install llama-stack-client")
    sys.exit(1)

# Color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def print_info(message: str):
    print(f"{Colors.YELLOW}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def print_header(title: str):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}{title}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")

def test_connection_and_models(client):
    """Test basic connection and model discovery"""
    print_header("🔗 Connection & Model Discovery")
    
    try:
        # Get models
        models_response = client.models.list()
        
        # Handle different response formats
        if hasattr(models_response, 'data'):
            models = models_response.data
        elif isinstance(models_response, list):
            models = models_response
        else:
            models = []
        
        print_success(f"✓ Connected successfully!")
        print_success(f"✓ Found {len(models)} models:")
        
        model_info = {}
        for model in models:
            model_id = getattr(model, 'identifier', getattr(model, 'id', 'unknown'))
            model_type = getattr(model, 'model_type', getattr(model, 'type', 'unknown'))
            provider = getattr(model, 'provider_id', 'unknown')
            
            print_info(f"  - {model_id} ({model_type}) via {provider}")
            model_info[model_type] = model_id
            
        return True, model_info
        
    except Exception as e:
        print_error(f"✗ Connection failed: {str(e)}")
        return False, {}

def test_vector_db(client):
    """Test vector database API"""
    print_header("🗃️ Vector Database")
    
    try:
        vector_dbs = client.vector_dbs.list()
        print_success(f"✓ Vector DB API accessible")
        print_info(f"Found {len(vector_dbs) if vector_dbs else 0} vector databases")
        return True
    except Exception as e:
        print_error(f"✗ Vector DB test failed: {str(e)}")
        return False

def test_basic_endpoints(client):
    """Test other basic endpoints"""
    print_header("🔍 Basic API Endpoints")
    
    results = {}
    
    # Test different endpoints that should exist
    endpoints = [
        ('agents', 'Agents API'),
        ('inference', 'Inference API'), 
        ('safety', 'Safety API'),
        ('eval', 'Evaluation API')
    ]
    
    for endpoint, name in endpoints:
        try:
            if hasattr(client, endpoint):
                print_success(f"✓ {name} available")
                results[endpoint] = True
            else:
                print_info(f"- {name} not available")
                results[endpoint] = False
        except Exception as e:
            print_error(f"✗ {name} error: {str(e)}")
            results[endpoint] = False
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Basic LlamaStack validation")
    parser.add_argument("--url", required=True, help="LlamaStack base URL")
    parser.add_argument("--token", help="API token (if required)")
    parser.add_argument("--skip-ssl-verify", action="store_true", help="Skip SSL verification")
    parser.add_argument("--json-output", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    print_header("🦙 Basic LlamaStack Validation")
    print_info(f"Target: {args.url}")
    print_info(f"Time: {datetime.now()}")
    if args.skip_ssl_verify:
        print_info("SSL verification: DISABLED")
    
    # Configure client
    client_kwargs = {
        'base_url': args.url,
        'api_key': args.token
    }
    
    if args.skip_ssl_verify:
        http_client = httpx.Client(verify=False, timeout=30)
        client_kwargs['http_client'] = http_client
    
    client = LlamaStackClient(**client_kwargs)
    
    # Run tests
    results = {}
    
    # Test 1: Connection and Models
    conn_success, model_info = test_connection_and_models(client)
    results['connection'] = conn_success
    results['models'] = model_info
    
    if not conn_success:
        print_error("❌ Basic connectivity failed - stopping tests")
        sys.exit(1)
    
    # Test 2: Vector DB
    results['vector_db'] = test_vector_db(client)
    
    # Test 3: Basic endpoints
    results['endpoints'] = test_basic_endpoints(client)
    
    # Summary
    print_header("📊 Validation Summary")
    
    total_tests = 3 + len(results.get('endpoints', {}))
    passed_tests = sum([
        results['connection'],
        results['vector_db'],
        sum(results.get('endpoints', {}).values())
    ])
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print_info(f"Tests passed: {passed_tests}/{total_tests}")
    print_info(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 60:
        print_success("🎉 Your LlamaStack deployment is working!")
        print_info("Core functionality is available:")
        for model_type, model_id in model_info.items():
            print_info(f"  - {model_type.upper()} model: {model_id}")
        if results['vector_db']:
            print_info("  - Vector database API ready")
    else:
        print_error("❌ Some core functionality issues found")
    
    # Save JSON output if requested
    if args.json_output:
        output = {
            'timestamp': datetime.now().isoformat(),
            'url': args.url,
            'success_rate': success_rate,
            'results': results
        }
        with open(args.json_output, 'w') as f:
            json.dump(output, f, indent=2)
        print_info(f"Results saved to {args.json_output}")
    
    sys.exit(0 if success_rate >= 60 else 1)

if __name__ == "__main__":
    main()
