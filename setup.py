from setuptools import setup, find_packages

setup(
    name="mcafee-sync",
    version="2.0.0",
    author="Stuart Graham",
    author_email="stuart@stuart-graham.com",
    description="Synchronize HTTP directory structures with local storage",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/stuartgraham/McAfeeUpdate",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "mcafee-sync=mcafee_sync.__main__:main",
        ],
    },
)
