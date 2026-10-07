"""flowpilot - event-driven AI automation: classify -> extract -> route -> act, with retries, dedupe, DLQ and human approval."""
from .engine import Engine, Workflow, load_workflow
from .store import Store

__all__ = ["Engine", "Workflow", "Store", "load_workflow"]
__version__ = "0.1.0"
