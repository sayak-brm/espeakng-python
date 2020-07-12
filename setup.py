import setuptools

with open("README.md", "r") as rm:
    long_description = rm.read()

setuptools.setup(
    name="espeakng",
    version="1.0.1",
    author="Sayak B",
    author_email="me@sayakb.com",
    description="An eSpeak NG TTS binding for Python3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["tts", "espeak", "speakng", "speech"],
    url="https://sayak-brm.github.io/espeakng-python/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.5",
)
