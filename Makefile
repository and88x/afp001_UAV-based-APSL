PY=python 
.PHONY:
    run
    all
    typehint
    test
    lint
    black
    clean
    install

run:
	$(PY) src/main.py 0 0

all:
	@+make black
	@+make typehint
	@+make lint
	#@+make test
	#@+make clean
	@+make run

typehint:
	mypy --ignore-missing-imports src/

test:
	# pytest tests/
	$(PY) src/runner.py

lint:
	pylint src/

black:
	black -l 79 src/*.py

clean:
	find . -type f -name "*.pyc" | xargs rm -fr 
	find . -type d -name __pycache__ | xargs rm -fr

install:
	pip install appdirs==1.4.4 astroid==2.6.1 certifi==2021.5.30 click==8.0.1 colorama==0.4.4 docopt==0.6.2 future==0.15.2 isort==5.9.1 lazy-object-proxy==1.6.0 lxml==4.6.3 mccabe==0.6.1 monotonic==1.6 mypy==0.910 mypy-extensions==0.4.3 pathspec==0.8.1 psutil==5.8.0 pymavlink==2.2.21 regex==2021.4.4 six==1.16.0 toml==0.10.2 typing-extensions==3.10.0.0 wincertstore==0.2 wrapt==1.12.1
	pip install dronekit==2.9.2 dronekit-sitl==3.3.0 matplotlib==2.2.5 pylint==2.9.0 black==21.6b0 py-make==0.1.1
	#python -m pip install wxpython