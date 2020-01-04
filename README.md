# aiozyre
asyncio-friendly Python bindings for [Zyre](https://github.com/zeromq/zyre), an open-source framework for proximity-based peer-to-peer applications.

![build_status](https://travis-ci.org/elijahr/aiozyre.svg?branch=master)

## Installation

```shell
pip install aiozyre
```

Tests run on both Linux and OS X for the following Python versions:
* CPython: 3.6.4, 3.7.0, 3.8.0, 3.9-dev

CPython 3.6.3 and lower are not supported due to [this bug](https://bugs.python.org/issue20891).

## Usage

See the [examples](https://github.com/elijahr/aiozyre/tree/master/examples).

## Contributing

Pull requests are welcome. You should be able to develop with something like:

```
git clone https://github.com/elijahr/aiozyre.git
cd aiozyre
pip install pipenv
pipenv install --three --dev
alias prp=pipenv run python
prp setup.py develop --uninstall; prp setup.py clean; prp setup.py build; prp setup.py develop; prp tests/__init__.py
```

Anytime you make changes to the .pyx or .pxd files, just re-run:
```
prp setup.py develop --uninstall; prp setup.py clean; prp setup.py build; prp setup.py develop; prp tests/__init__.py
```
