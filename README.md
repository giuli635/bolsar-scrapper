# ***Bolsar Scrapper***

Just a simple library and script written in Python to obtain basic information from <https://www.bolsar.info> about the financial market in Argentina. Since bolsar doesn't have an API and the great majority of its content it's javascript generated, the only option to use to reach the objetive was Selenium. In this project I use Selenium specifically with Firefox with no reason other than personal preference.
The provided installation script allows to automate the installation of this library in a python virtual environment in Arch Linux, this includes system dependencies and python dependencies.
In case you have or want to do this process manually you must have Firefox, it's [driver for selenium](https://github.com/mozilla/geckodriver), python and pip installed in your system.
Then you just have to clone this repo, `cd` into its directory:

```bash
git clone https://github.com/giuli635/bolsar-scrapper.git
cd bolsar-scrapper
```

Install the build python library and build the package:

```bash
pip install build
python -m build
```

After that you only have to run the following:

```bash
pip install dist/bolsar_scrapper-0.0.1-py3-none-any.whl
```

This software also comes with a script (located into the script folder) to use it as a command, in this case, to access it from all over your system you could add it to `/usr/local/bin`.
