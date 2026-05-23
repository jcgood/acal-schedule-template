.PHONY: build check match roster doctor

build:
	python conf.py build

match:
	python conf.py match

check:
	python conf.py check

roster:
	python conf.py roster

doctor:
	python conf.py doctor
