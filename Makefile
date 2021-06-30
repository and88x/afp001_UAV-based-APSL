PY=python 
.PHONY:
    run
    all
    typehint
    test
    lint
    black
    clean

run:
	$(PY) src/main.py

all:
	@+make typehint
	#@+make test
	@+make black
	@+make clean
	@+make lint
	@+make run

typehint:
	mypy --ignore-missing-imports src/

test:
	pytest tests/

lint:
	pylint src/

black:
	black -l 79 src/*.py

clean:
	#find . -type f -name "*.pyc" | xargs rm -fr 
	find . -type d -name __pycache__ | xargs rm -fr
