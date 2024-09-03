from setuptools import setup, find_packages
from setuptools.command.install import install
import requests
import zipfile

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

#print("zzzzzzz", find_packages(include=["metamorphosed", "coref"]))

# installs jquery etc. once metamorphosed is installed
class postinstall(install):
    def run(self):
        install.run(self)
        guipath = os.path.join(self.install_libbase, self.config_vars.get("dist_name"), "gui", "lib")
        os.makedirs(guipath, exist_ok=True)

        self.installjq("https://code.jquery.com/jquery-3.6.0.min.js", os.path.join(guipath, "jquery-3.6.0.min.js"))
        self.installjq("https://code.jquery.com/jquery-3.6.0.min.js", os.path.join(guipath, "jquery-3.6.0.min.js"))
        self.installjq("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.js", os.path.join(guipath, "jquery.modal-0.9.2.min.js"))
        self.installjq("https://cdnjs.cloudflare.com/ajax/libs/jquery-modal/0.9.2/jquery.modal.min.css", os.path.join(guipath, "jquery.modal-0.9.2.min.css"))
        self.installjq("https://jqueryui.com/resources/download/jquery-ui-1.13.2.zip", os.path.join(guipath, "query-ui-1.13.2.zip"))
        self.unzip(os.path.join(guipath, "query-ui-1.13.2.zip"), guipath)

    def installjq(self, url, fn):
        r = requests.get(url)
        f = open(fn, "wb")
        f.write(r.content)
        f.close()

    def unzip(self, fn, outdir):
        with zipfile.ZipFile(fn, 'r') as zip_ref:
            zip_ref.extractall(outdir)


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
    cmdclass={ "install": postinstall},
    #package_data={"metamorphosed": ["metamorphosed/gui/*.html",
    #                                "metamorphosed/gui/*.js",
    #                                "metamorphosed/gui/*.css",
    #                                "metamorphosed/gui/img/*",
    #                                ]}
    )

