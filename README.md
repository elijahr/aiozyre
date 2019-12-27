![build_status](https://travis-ci.org/elijahr/aiozyre.svg?branch=master)

# aiozyre
asyncio-friendly Python bindings for Zyre

## Installing

The package is in pypi, you can install it with:
```
pip install aiozyre
```

CPython 3.5, 3.6, 3.7, and 3.8 are supported on Linux and OS X.

## Usage

See `tests/__init__.py` for examples.

## Contributing

Pull requests are welcome. If you have a suggestion or a question please post an issue.
The bindings to Zyre are written in Cython. You should be able to develop with something like:

```
git clone https://github.com/elijahr/aiozyre.git
cd aiozyre
pip install pipenv
pipenv install --three --dev
pipenv run python tests/__init__.py
```
