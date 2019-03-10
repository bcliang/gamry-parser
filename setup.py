import io
from setuptools import find_packages, setup

main_ns = {}
exec(open('gamry_parser/version.py').read(), main_ns)

setup(
    name="gamry_parser",
    version=main_ns['__version__'],
    description="Package for parsing the contents of Gamry EXPLAIN data (DTA) files.",
    author="Brad Liang",
    author_email='brad.liang@percusense.com',
    url="https://github.com/bcliang/gamry-parser",
    license='MIT',
    packages=find_packages(),
    long_description=io.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'pandas'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
