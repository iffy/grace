

help:
	cat Makefile


clean:
	-find . -name "*.pyc" -exec rm {} \;
	-rm -r _trial_temp
