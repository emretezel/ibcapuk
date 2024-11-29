from setuptools import setup, find_packages

setup(
    name="ibcapuk",  # Replace with your package name
    version="0.1.0",  # Initial version
    description="A package for calculating capital gains and losses based on Interactive Broker statements for UK "
    "residents.",  # Short description
    author="Emre Tezel",  # Your name
    author_email="emre.tezel@gmail.com",  # Your email
    packages=find_packages(),  # Automatically find packages in the directory
    install_requires=[
        "beautifulsoup4>=4.12.3",
        "numpy>=1.26.4",
        "pandas>=2.2.2",
        "setuptools>=75.1.0",
        "tabulate>=0.9.0",
        "fpdf2>=2.8.1",
    ],  # List dependencies here (initially empty)
    python_requires=">=3.12",  # Specify Python version compatibility
)
