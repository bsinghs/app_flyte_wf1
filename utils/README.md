# 🛠️ Flyte Workflow Utilities

This directory contains utility scripts for monitoring and analyzing Flyte workflow resources.

## 📋 Available Tools

### 1. Resource Summary (`resource_summary.py`)
**Purpose**: Extracts and displays CPU/memory resource configurations from workflow Python files

**Usage**:
```bash
# Analyze default file (ml_pipeline_improved.py)
python utils/resource_summary.py

# Analyze specific file
python utils/resource_summary.py my_workflow.py
```

**Output**: Clean, formatted list of all task resources with helpful explanations

**Example Output**:
```
============================================================
🚀 FLYTE WORKFLOW RESOURCE SUMMARY
============================================================

📋 load_data:        (requests 500m CPU, 500Mi memory, limits 1 CPU, 1Gi memory)
📋 clean_data:       (requests 200m CPU, 200Mi memory, limits 500m CPU, 500Mi memory)
📋 features:         (requests 300m CPU, 300Mi memory, limits 500m CPU, 500Mi memory)
📋 train_model:      (requests 800m CPU, 800Mi memory, limits 1 CPU, 1Gi memory)
📋 evaluate_model:   (requests 200m CPU, 200Mi memory, limits 500m CPU, 500Mi memory)
```

---

### 2. Resource Reference Card (`resource_card.py`)
**Purpose**: Displays a beautiful visual summary with totals and cluster analysis

**Usage**:
```bash
python utils/resource_card.py
```

**Features**:
- Beautiful ASCII art table format
- Total resource calculations
- Cluster sizing recommendations
- Quick reference information

**Example Output**:
```
╔══════════════════════════════════════════════════════════════════════╗
║                    🚀 ML WORKFLOW RESOURCE CARD                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  📋 load_data        │ 500m CPU, 500Mi RAM  │ max: 1 CPU, 1Gi RAM   ║
║  📋 clean_data       │ 200m CPU, 200Mi RAM  │ max: 500m CPU, 500Mi   ║
║  📋 train_model      │ 800m CPU, 800Mi RAM  │ max: 1 CPU, 1Gi RAM    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

### 3. Live Execution Monitor (`live_execution_monitor.py`)
**Purpose**: Fetches actual resource usage from Kubernetes pods for running/completed executions

**Usage**:
```bash
python utils/live_execution_monitor.py <execution-id>

# Example:
python utils/live_execution_monitor.py aj84ckgrqc52cs82zq4q
```

**Features**:
- Real-time pod status monitoring
- Actual resource allocations from Kubernetes
- Pod success/failure status
- Useful for debugging resource-related issues

**Requirements**:
- `kubectl` configured for your Flyte cluster
- Access to the Kubernetes namespace where Flyte runs

---

## 🎯 Quick Start Guide

### For Daily Use:
```bash
# Quick overview of your workflow resources
python utils/resource_card.py

# Detailed analysis
python utils/resource_summary.py
```

### For Debugging Executions:
```bash
# Monitor a specific execution
python utils/live_execution_monitor.py <execution-id>
```

### For Resource Planning:
1. Run `resource_card.py` to see total requirements
2. Use the "Cluster Requirements" section for node sizing
3. Adjust resources in `ml_pipeline_improved.py` as needed

---

## 📁 Generated Files

These utilities may create output files in this directory:

- `resource_summary.txt` - Output from resource_summary.py
- `execution_resources_<execution-id>.txt` - Output from live_execution_monitor.py

---

## 🔧 Modifying Resources

To change task resource allocations, edit the `@task` decorators in your workflow files:

```python
@task(requests=Resources(cpu="500m", mem="500Mi"), limits=Resources(cpu="1", mem="1Gi"))
def my_task():
    # task implementation
```

**Key Points**:
- `requests` = guaranteed minimum resources
- `limits` = maximum allowed resources  
- CPU: `1000m` = 1 core, `500m` = 0.5 cores
- Memory: `Mi` = mebibytes, `Gi` = gibibytes

---

## 🚨 Troubleshooting

### "No pods found for this execution"
- Pods may have been garbage collected
- Check if execution ID is correct
- Ensure kubectl is configured properly

### "No resource configurations found"
- Check if your workflow file has `@task` decorators with `Resources`
- Verify file path is correct
- Make sure the Python file is syntactically valid

### Performance Issues
- If tasks are pending/failing, check if cluster has enough resources
- Use `kubectl get nodes` to check available cluster capacity
- Reduce resource requests if cluster is small

---

## 🔗 Related Documentation

- Main project README: `../README.md`
- Flyte documentation: `../docs/`
- OAuth learning materials: `../oauth-learning/`

---

*These utilities complement the Flyte UI by providing better resource visibility and analysis capabilities.*
