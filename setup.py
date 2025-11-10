from setuptools import setup, find_packages

setup(
    name="flowkestra",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml",
        "paramiko",
        "scikit-learn",  # optional, for example scripts
        "mlflow"
    ],
    entry_points={
        "console_scripts": [
            "flowkestra=flowkestra.cli:main"
        ]
    },
    python_requires=">=3.8",
)
