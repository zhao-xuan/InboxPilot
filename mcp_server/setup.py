#!/usr/bin/env python3
"""
Setup script for Microsoft Graph MCP Server
"""

from setuptools import setup, find_packages

setup(
    name="microsoft-graph-mcp-server",
    version="1.0.0",
    description="MCP Server for Microsoft Graph API integration",
    author="AI Assistant",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.25.0",
        "mcp>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "microsoft-graph-mcp-server=microsoft_graph_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 