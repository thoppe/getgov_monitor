process:
	python P0_clone_and_extract.py
	python P1_compile_results.py
	git add data/changelog

lint:
	black *.py
	flake8 *.py
