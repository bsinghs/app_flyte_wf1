#!/usr/bin/env python3
"""
Quick Resource Reference Card
A simple reference for your workflow resource configurations
"""

def print_resource_card():
    """Print a quick resource reference card"""
    
    card = """
╔══════════════════════════════════════════════════════════════════════╗
║                    🚀 ML WORKFLOW RESOURCE CARD                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  📋 load_data        │ 500m CPU, 500Mi RAM  │ max: 1 CPU, 1Gi RAM   ║
║  📋 clean_data       │ 200m CPU, 200Mi RAM  │ max: 500m CPU, 500Mi   ║
║  📋 features         │ 300m CPU, 300Mi RAM  │ max: 500m CPU, 500Mi   ║
║  📋 train_model      │ 800m CPU, 800Mi RAM  │ max: 1 CPU, 1Gi RAM    ║
║  📋 evaluate_model   │ 200m CPU, 200Mi RAM  │ max: 500m CPU, 500Mi   ║
║                                                                      ║
║  📊 Total Requests: 2.0 CPU, 2000Mi RAM (~2Gi)                      ║
║  🚨 Total Limits:   3.5 CPU, 3500Mi RAM (~3.5Gi)                    ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  💡 Quick Reference:                                                 ║
║     • 1000m = 1 CPU core                                             ║
║     • 1024Mi = 1Gi (approximately)                                   ║
║     • Requests = guaranteed minimum                                  ║
║     • Limits = maximum allowed                                       ║
║                                                                      ║
║  🔧 To modify resources, edit ml_pipeline_improved.py:              ║
║     @task(requests=Resources(cpu="500m", mem="500Mi"))              ║
║                                                                      ║
║  📈 Monitoring:                                                      ║
║     • UI: Individual task details (JSON format)                     ║
║     • CLI: python resource_summary.py                               ║
║     • Live: python live_execution_monitor.py <execution-id>         ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(card)
    
    # Calculate some useful stats
    total_requests_cpu = 500 + 200 + 300 + 800 + 200  # millicores
    total_requests_mem = 500 + 200 + 300 + 800 + 200  # Mi
    
    total_limits_cpu = 1000 + 500 + 500 + 1000 + 500  # millicores
    total_limits_mem = 1024 + 500 + 500 + 1024 + 500  # Mi (1Gi = 1024Mi)
    
    print(f"📈 Resource Analysis:")
    print(f"   • Peak CPU usage: {total_requests_cpu}m ({total_requests_cpu/1000:.1f} cores)")
    print(f"   • Peak Memory usage: {total_requests_mem}Mi ({total_requests_mem/1024:.1f}Gi)")
    print(f"   • Max possible CPU: {total_limits_cpu}m ({total_limits_cpu/1000:.1f} cores)")
    print(f"   • Max possible Memory: {total_limits_mem}Mi ({total_limits_mem/1024:.1f}Gi)")
    print()
    print(f"🎯 Cluster Requirements:")
    print(f"   • Minimum node size: {total_requests_cpu/1000:.1f} CPU, {total_requests_mem/1024:.1f}Gi RAM")
    print(f"   • Recommended node size: {total_limits_cpu/1000:.1f} CPU, {total_limits_mem/1024:.1f}Gi RAM")


if __name__ == "__main__":
    print_resource_card()
