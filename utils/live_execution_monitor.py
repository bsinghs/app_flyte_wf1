#!/usr/bin/env python3
"""
Live Flyte Execution Resource Monitor
Fetches actual resource usage from Kubernetes pods for running/completed executions
"""

import subprocess
import json
import sys
from typing import Dict, List, Any, Optional


def get_execution_pods(execution_id: str, namespace: str = "flyte") -> List[Dict[str, Any]]:
    """Get all pods associated with a Flyte execution"""
    
    try:
        # Get pods with the execution ID label
        cmd = [
            "kubectl", "get", "pods", 
            "-n", namespace,
            "-l", f"execution-id={execution_id}",
            "-o", "json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pods_data = json.loads(result.stdout)
        
        return pods_data.get("items", [])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting pods: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing kubectl output: {e}")
        return []


def extract_pod_resources(pod: Dict[str, Any]) -> Dict[str, Any]:
    """Extract resource information from a pod specification"""
    
    resources = {}
    
    # Get pod name and labels
    pod_name = pod.get("metadata", {}).get("name", "unknown")
    labels = pod.get("metadata", {}).get("labels", {})
    task_name = labels.get("task-name", "unknown")
    
    # Get container resources
    containers = pod.get("spec", {}).get("containers", [])
    if containers:
        container = containers[0]  # Usually just one container
        container_resources = container.get("resources", {})
        
        resources = {
            "pod_name": pod_name,
            "task_name": task_name,
            "requests": container_resources.get("requests", {}),
            "limits": container_resources.get("limits", {}),
            "status": pod.get("status", {}).get("phase", "unknown")
        }
    
    return resources


def format_execution_resources(execution_id: str, pod_resources: List[Dict[str, Any]]) -> str:
    """Format execution resource information for display"""
    
    output = []
    output.append("=" * 70)
    output.append(f"🎯 FLYTE EXECUTION RESOURCE USAGE")
    output.append(f"📋 Execution ID: {execution_id}")
    output.append("=" * 70)
    output.append("")
    
    if not pod_resources:
        output.append("❌ No pods found for this execution")
        output.append("   • Check if the execution ID is correct")
        output.append("   • Ensure kubectl is configured for your cluster")
        return "\n".join(output)
    
    # Group by task name
    task_groups = {}
    for resource in pod_resources:
        task_name = resource["task_name"]
        if task_name not in task_groups:
            task_groups[task_name] = []
        task_groups[task_name].append(resource)
    
    for task_name, pods in task_groups.items():
        output.append(f"🔧 Task: {task_name}")
        
        for pod in pods:
            status_emoji = "✅" if pod["status"] == "Succeeded" else "🔄" if pod["status"] == "Running" else "❌"
            output.append(f"   {status_emoji} Pod: {pod['pod_name'][:20]}... (Status: {pod['status']})")
            
            requests = pod["requests"]
            limits = pod["limits"]
            
            if requests or limits:
                resource_lines = []
                
                if requests:
                    req_parts = []
                    if "cpu" in requests:
                        req_parts.append(f"CPU: {requests['cpu']}")
                    if "memory" in requests:
                        req_parts.append(f"Memory: {requests['memory']}")
                    if req_parts:
                        resource_lines.append(f"      📊 Requests: {', '.join(req_parts)}")
                
                if limits:
                    lim_parts = []
                    if "cpu" in limits:
                        lim_parts.append(f"CPU: {limits['cpu']}")
                    if "memory" in limits:
                        lim_parts.append(f"Memory: {limits['memory']}")
                    if lim_parts:
                        resource_lines.append(f"      🚨 Limits:   {', '.join(lim_parts)}")
                
                output.extend(resource_lines)
            else:
                output.append("      ⚠️  No resource specifications found")
            
            output.append("")
    
    output.append("💡 Legend:")
    output.append("   ✅ Succeeded  🔄 Running  ❌ Failed/Pending")
    output.append("   📊 Requests = guaranteed resources")
    output.append("   🚨 Limits = maximum allowed resources")
    output.append("")
    
    return "\n".join(output)


def main():
    """Main function"""
    
    if len(sys.argv) != 2:
        print("Usage: python live_execution_monitor.py <execution-id>")
        print("Example: python live_execution_monitor.py aj84ckgrqc52cs82zq4q")
        return
    
    execution_id = sys.argv[1]
    
    print(f"🔍 Fetching resource information for execution: {execution_id}")
    print("⏳ This may take a few seconds...")
    print("")
    
    # Get pods for the execution
    pods = get_execution_pods(execution_id)
    
    # Extract resource information
    pod_resources = []
    for pod in pods:
        resource_info = extract_pod_resources(pod)
        if resource_info:
            pod_resources.append(resource_info)
    
    # Format and display
    summary = format_execution_resources(execution_id, pod_resources)
    print(summary)
    
    # Save to file
    filename = f"execution_resources_{execution_id}.txt"
    with open(filename, "w") as f:
        f.write(summary)
    print(f"📄 Summary saved to: {filename}")


if __name__ == "__main__":
    main()
