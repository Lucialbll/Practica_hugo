.PHONY: index build clean

index:
	python tools/index.py

build: index
	hugo

clean: