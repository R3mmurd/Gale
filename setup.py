import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Gale",
    version="0.0.2",
    author="Alejandro Mujica",
    author_email="aledrums@gmail.com",
    description="Collection of reusable codes to make games by using pygame",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/R3mmurd/gale",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=['wheel', 'pygame', 'click'],
    )
)
