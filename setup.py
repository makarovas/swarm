"""
Установочный скрипт для системы агентного роевого программирования
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="swarm-programming",
    version="1.0.0",
    author="Swarm Development Team",
    author_email="team@swarm-programming.dev",
    description="Система агентного роевого программирования",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swarm-programming/swarm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="swarm, multi-agent, collective-intelligence, distributed-computing, programming",
    project_urls={
        "Bug Reports": "https://github.com/swarm-programming/swarm/issues",
        "Source": "https://github.com/swarm-programming/swarm",
        "Documentation": "https://swarm-programming.readthedocs.io/",
    },
)
