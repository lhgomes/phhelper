# coding: utf-8
import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='phhelper',
    version='0.9.17',
    author='Luiz Henrique Gomes',
    author_email="lhgnet@gmail.com",
    description='Python Handler Helper for Lambda',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url="https://github.com/lhgomes/phhelper",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    license='MIT',
)
