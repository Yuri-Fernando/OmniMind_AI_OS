"""Loader de ferramentas — registra e expõe todas as tools disponíveis."""
from tools.web_search import WebSearchTool
from tools.file_reader import FileReaderTool
from tools.web_scraper import WebScraperTool
from tools.code_executor import CodeExecutorTool
from tools.calculator import CalculatorTool
from tools.weather_api import WeatherAPITool
from tools.auto_tool_discovery import AutoToolDiscoveryTool, discover_tools


class ToolLoader:
    def __init__(self):
        self.tools = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        self.register_tool("web_search", WebSearchTool())
        self.register_tool("file_reader", FileReaderTool())
        self.register_tool("web_scraper", WebScraperTool())
        self.register_tool("code_executor", CodeExecutorTool())
        self.register_tool("calculator", CalculatorTool())
        self.register_tool("weather", WeatherAPITool())
        self.register_tool("auto_tool_discovery", AutoToolDiscoveryTool())

        # Descobrimento automático de tools adicionais
        auto_discovered = discover_tools()
        for name, tool in auto_discovered.items():
            if name not in self.tools:
                self.register_tool(name, tool)

    def register_tool(self, name: str, tool_instance):
        self.tools[name] = tool_instance

    def get_tool(self, tool_name: str):
        tool = self.tools.get(tool_name)
        if tool is None:
            raise KeyError(f"Tool '{tool_name}' não encontrada. Disponíveis: {list(self.tools.keys())}")
        return tool

    def list_tools(self):
        return list(self.tools.keys())
