from setuptools import setup

setup(
    name='hurricanesoft-api',
    version='0.1.0',
    packages=['hurricanesoft_api'],
    package_dir={'hurricanesoft_api': '.'},
    python_requires='>=3.8',
    install_requires=[
        'hurricanesoft-cli',
        'hurricanesoft-auth',
    ],
    extras_require={
        'pg': ['psycopg2-binary'],
    },
    entry_points={
        'console_scripts': [
            'hurricanesoft-api=hurricanesoft_api.server:main',
        ],
    },
    author='Sonia',
    author_email='sonia@hurricanesoft.com.tw',
    description='HurricaneSoft Unified API Server',
)
