import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="netxms",
    version="2.2.12",
    author="Alex Kirhenshtein",
    author_email="alk@netxms.org",
    description="NetXMS Client Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://netxms.org",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3",
        "Operating System :: OS Independent",
    ],
)