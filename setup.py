from setuptools import setup, find_packages

setup(
    name="schemaorg-arc-builder",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "python-dotenv",
        "arctrl",
        "rocrate",
    ],
    entry_points={
        "console_scripts": [
            "harvest-process = scripts.harvest.harvest_and_process:main",
        ],
    },
)