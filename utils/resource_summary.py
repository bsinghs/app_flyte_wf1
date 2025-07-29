#!/usr/bin/env python3
"""
Resource Summary Tool for Flyte Workflows
Extracts and displays CPU/memory resource configurations from your workflow tasks
"""

import ast
import re
from typing import Dict, Any, Optional


def extract_resource_info(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Extract resource information from a Python workflow file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the AST to find task decorators
    tree = ast.parse(content)
    
    task_resources = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if this function has a @task decorator
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    if decorator.func.id == 'task':
                        # Extract resource information from the decorator
                        task_name = node.name
                        resources = extract_resources_from_decorator(decorator)
                        if resources:
                            task_resources[task_name] = resources
    
    return task_resources


def extract_resources_from_decorator(decorator: ast.Call) -> Optional[Dict[str, Any]]:
    """Extract resource information from a @task decorator"""
    
    resources_info = {}
    
    for keyword in decorator.keywords:
        if keyword.arg in ['requests', 'limits']:
            if isinstance(keyword.value, ast.Call) and isinstance(keyword.value.func, ast.Name):
                if keyword.value.func.id == 'Resources':
                    resource_values = {}
                    for kw in keyword.value.keywords:
                        if isinstance(kw.value, ast.Constant):
                            resource_values[kw.arg] = kw.value.value
                    resources_info[keyword.arg] = resource_values
    
    return resources_info if resources_info else None


def format_resource_display(task_resources: Dict[str, Dict[str, Any]]) -> str:
    """Format resource information for display"""
    
    output = []
    output.append("=" * 60)
    output.append("🚀 FLYTE WORKFLOW RESOURCE SUMMARY")
    output.append("=" * 60)
    output.append("")
    
    if not task_resources:
        output.append("❌ No resource configurations found in the workflow")
        return "\n".join(output)
    
    # Find the longest task name for alignment
    max_name_length = max(len(name) for name in task_resources.keys())
    
    for task_name, resources in task_resources.items():
        # Format task name with proper alignment
        formatted_name = f"📋 {task_name}:".ljust(max_name_length + 5)
        
        # Extract requests and limits
        requests = resources.get('requests', {})
        limits = resources.get('limits', {})
        
        # Build the resource string
        resource_parts = []
        
        if requests:
            req_parts = []
            if 'cpu' in requests:
                req_parts.append(f"{requests['cpu']} CPU")
            if 'mem' in requests:
                req_parts.append(f"{requests['mem']} memory")
            if req_parts:
                resource_parts.append(f"requests {', '.join(req_parts)}")
        
        if limits:
            lim_parts = []
            if 'cpu' in limits:
                lim_parts.append(f"{limits['cpu']} CPU")
            if 'mem' in limits:
                lim_parts.append(f"{limits['mem']} memory")
            if lim_parts:
                resource_parts.append(f"limits {', '.join(lim_parts)}")
        
        if resource_parts:
            resource_string = f" ({', '.join(resource_parts)})"
        else:
            resource_string = " (no resource limits specified)"
        
        output.append(f"{formatted_name}{resource_string}")
    
    output.append("")
    output.append("💡 Tips:")
    output.append("   • Requests = guaranteed resources")
    output.append("   • Limits = maximum allowed resources")
    output.append("   • CPU: 1000m = 1 core, 500m = 0.5 cores")
    output.append("   • Memory: Mi = mebibytes, Gi = gibibytes")
    output.append("")
    
    return "\n".join(output)


def main():
    """Main function to generate resource summary"""
    
    import sys
    import os
    
    # Default to ml_pipeline_improved.py if no argument provided
    if len(sys.argv) > 1:
        workflow_file = sys.argv[1]
    else:
        workflow_file = "ml_pipeline_improved.py"
    
    if not os.path.exists(workflow_file):
        print(f"❌ Error: File '{workflow_file}' not found")
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📝 Available Python files:")
        for f in os.listdir("."):
            if f.endswith(".py"):
                print(f"   • {f}")
        return
    
    try:
        task_resources = extract_resource_info(workflow_file)
        summary = format_resource_display(task_resources)
        print(summary)
        
        # Also save to a file for reference
        with open("resource_summary.txt", "w") as f:
            f.write(summary)
        print(f"📄 Summary also saved to: resource_summary.txt")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
