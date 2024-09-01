from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

print("zzzzzzz", find_packages(include=["metamorphosed", "coref"]))

setup(
    name="metamorphosed",
    version="3.6.0",
    description="A graphical Abstract Meaning Represention Editor",
    url="https://github.com/Orange-Opensource/metamorphosed.git",
    author="Johannes Heinecke",
    author_email="johannes.heinecke@orange.com",
    license="BSD3-Clause License",
    packages=find_packages(include=["metamorphosed", "coref"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    install_requires=["pytest==7.4.0",
                      "werkzeug==3.0.3",
                      "Flask==3.0.2",
                      "Flask-Cors==4.0.1",
                      "graphviz==0.20.1",
                      "Penman==1.3.0",
                      "GitPython==3.1.42",
                      "PyYAML==6.0.1",
                      "requests==2.32.3",
                      "smatchpp==1.7.0"],

    classifiers=["License :: OSI Approved :: BSD 3-Clause License",
                 "Topic :: Text Processing :: Linguistic",
                 "Programming Language :: Python :: 3.10"],
    scripts=["metamorphosed_server.py"],
    include_package_data=True,
    #package_data={"metamorphosed": ["metamorphosed/gui/*.html",
    #                                "metamorphosed/gui/*.js",
    #                                "metamorphosed/gui/*.css",
    #                                "metamorphosed/gui/img/*",
    #                                ]}
    )

#import requests
#def installjq(url, fn):
#    r = requests.get(url)
#    f = open(fn, "wb")
#    f.write(r.content)
#    f.close()
#
#installjq("https://code.jquery.com/jquery-3.6.0.min.js", "jquery-3.6.0.min.js")
