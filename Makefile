all::   pyboard.py
	python3 pyboard.py -d /dev/ttyUSB0 donationslapper.py


pyboard.py:
	curl -O 'https://raw.githubusercontent.com/micropython/micropython/master/tools/pyboard.py'
