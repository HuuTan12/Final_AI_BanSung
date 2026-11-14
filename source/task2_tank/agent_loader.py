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

    DEFAULT_EXTERNAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "external")

    @staticmethod
    def load_agent_from_file(file_path: str, depth: Optional[int] = None) -> Optional[BaseAgent]:
        """
        Dynamically loads an agent inheriting from BaseAgent from a specified Python file.
        Returns an instance of the agent, or None if loading fails.
        """
        if not os.path.exists(file_path):
            print(f"[AgentLoader] Error: File '{file_path}' does not exist.")
            return None

        abs_path = os.path.abspath(file_path)
        try:
            base_name = os.path.splitext(os.path.basename(abs_path))[0]
            module_name = f"external_agent_{abs(hash(abs_path))}_{base_name}"
            spec = importlib.util.spec_from_file_location(module_name, abs_path)
            if spec is None or spec.loader is None:
                print(f"[AgentLoader] Error: Could not load spec for '{file_path}'.")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Inspect classes in module that inherit from BaseAgent (defined in this file)
            candidates = []
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAgent) and obj is not BaseAgent and obj.__module__ == module_name:
                    candidates.append(obj)
            if not candidates:
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                        candidates.append(obj)

            if candidates:
                cls = candidates[0]
                sig = inspect.signature(cls.__init__)
                if depth is not None and "depth" in sig.parameters:
                    agent_instance = cls(depth=depth)
                else:
                    agent_instance = cls()
                agent_instance.external_file_path = abs_path
                print(f"[AgentLoader] Successfully loaded external agent '{agent_instance.name}' from {file_path}")
                return agent_instance

            print(f"[AgentLoader] Warning: No subclass of BaseAgent found in '{file_path}'.")
            return None

        except Exception as e:
            print(f"[AgentLoader] Exception while loading '{file_path}': {e}")
            return None

    @classmethod
    def discover_external_agent_files(cls, folder_path: Optional[str] = None) -> List[str]:
        """Returns sorted absolute paths to .py agent files in the external directory."""
        target_dir = folder_path if folder_path is not None else cls.DEFAULT_EXTERNAL_DIR
        if not os.path.isdir(target_dir):
            return []

        files: List[str] = []
        for fname in sorted(os.listdir(target_dir)):
            if fname.endswith(".py") and not fname.startswith("__"):
                files.append(os.path.abspath(os.path.join(target_dir, fname)))
        return files

    @classmethod
    def discover_external_agents(cls, folder_path: Optional[str] = None) -> List[BaseAgent]:
        """
        Scans a directory for all .py files and instantiates every valid external agent found.
        """
        agents: List[BaseAgent] = []
        for fpath in cls.discover_external_agent_files(folder_path):
            agent = cls.load_agent_from_file(fpath)
            if agent is not None:
                agents.append(agent)
        return agents
