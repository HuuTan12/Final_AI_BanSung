"""
agent_loader.py - Dynamic Plugin Loader for External Student Agents
Course: Introduction to Artificial Intelligence (503043)
Author: Student Group
Description:
    Provides dynamic module loading (Req 3 - 0.5 pt) so algorithms developed
    by other student groups can be loaded from .py files and compete
    directly in the Tank Battle environment without modifying game code.
"""

import os
import sys
import importlib.util
import inspect
from typing import List, Optional

from task2_tank.agents.base_agent import BaseAgent


class AgentLoader:
    """
    Manages discovering and instantiating external agent implementations.
    """

    @staticmethod
    def load_agent_from_file(file_path: str) -> Optional[BaseAgent]:
        """
        Dynamically loads an agent inheriting from BaseAgent from a specified Python file.
        Returns an instance of the agent, or None if loading fails.
        """
        if not os.path.exists(file_path):
            print(f"[AgentLoader] Error: File '{file_path}' does not exist.")
            return None

        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                print(f"[AgentLoader] Error: Could not load spec for '{file_path}'.")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Inspect classes in module that inherit from BaseAgent
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    agent_instance = obj()
                    print(f"[AgentLoader] Successfully loaded external agent '{agent_instance.name}' from {file_path}")
                    return agent_instance

            print(f"[AgentLoader] Warning: No subclass of BaseAgent found in '{file_path}'.")
            return None

        except Exception as e:
            print(f"[AgentLoader] Exception while loading '{file_path}': {e}")
            return None

    @staticmethod
    def discover_external_agents(folder_path: str = "agents/external") -> List[BaseAgent]:
        """
        Scans a directory for all .py files and instantiates every valid external agent found.
        """
        agents: List[BaseAgent] = []
        if not os.path.isdir(folder_path):
            return agents

        for fname in sorted(os.listdir(folder_path)):
            if fname.endswith(".py") and not fname.startswith("__"):
                fpath = os.path.join(folder_path, fname)
                agent = AgentLoader.load_agent_from_file(fpath)
                if agent is not None:
                    agents.append(agent)

        return agents
