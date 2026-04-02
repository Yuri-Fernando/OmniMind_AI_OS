"""Registry de ferramentas — padrão Singleton."""
from tools.tool_loader import ToolLoader


class ToolRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.loader = ToolLoader()
        return cls._instance

    def get_tool(self, tool_name):
        return self.loader.get_tool(tool_name)

    def register_tool(self, name, tool_instance):
        self.loader.register_tool(name, tool_instance)

    def list_tools(self):
        return list(self.loader.tools.keys())


registry = ToolRegistry()
