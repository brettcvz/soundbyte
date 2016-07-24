.phony: run upgrade

run:
	sudo venv/bin/python soundbyte.py

upgrade:
	 pip install --upgrade git+https://github.com/brettcvz/MFRC522-python.git --process-dependency-links
