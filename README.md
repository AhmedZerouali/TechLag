# TechLag: technical lag of your Javascript package

TechLag is an utility that calculates how many updates your dependencies are missings.
For now, TechLag only supports npm packages.

## Requirements
- pandas>=0.22.0
- requests>=2.18.2

##  How to install/uninstall
TechLag is developed and tested mainly on GNU/Linux platforms. Thus it is very likely it will work out of the box
on any Linux-like (or Unix-like) platform, upon providing the right version of Python (3.5, 3.6).


**To install**, run:
```
$> git clone https://github.com/neglectos/TechLag
$> python3 setup.py build
$> python3 setup.py install
```

**To uninstall**, run:
```
$> pip3 uninstall techlag
```

## How to use

TechLag can be used from command line or directly from Python, both usages are described below.

### From command line
Launching TechLag from command line does not require much effort.

```
$ techlag -p grunt -v 1.0.0 -k dependencies
or
$ techlag -j https://raw.githubusercontent.com/jasmine/jasmine/master/package.json -k devDependencies
```

### From Python
TechLag can be embedded in your Python scripts. Again, the effort of using it is minimum.

```
#! /usr/bin/env python3
from techlag.techlag import TechLag

# With 3 parameters
tl = TechLag(package="grunt", version="1.0.0", kind="dependencies")
print(tl.analyze())

# Version can be a constraint as well
tl = TechLag(package="grunt", version="~1.0.0", kind="dependencies")
print(tl.analyze())

# With 2 parameters
tl = TechLag(pjson="https://raw.githubusercontent.com/jasmine/jasmine/master/package.json", kind="devDependencies")
print(tl.analyze())
```
