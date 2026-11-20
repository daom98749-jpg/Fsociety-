from setuptools import setup

setup(
    name="fsociety-toolkit",
    version="1.0.0",
    description="Network recon toolkit - IP info, port scan, DNS, WHOIS, HTTP header check",
    author="daom98749-jpg",
    license="MIT",
    py_modules=["fsociety_toolkit_v1"],
    python_requires=">=3.8",
    install_requires=[
        'colorama>=0.4.6; sys_platform == "win32"',
    ],
    entry_points={
        "console_scripts": [
            "fsociety-toolkit=fsociety_toolkit_v1:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
