install:
	pip3 install -r requirements.txt

type_check:
	python3 -m mypy scraping

scrape:
	python3 -m scraping scrape --email lorenzmax098@gmail.com

headless:
	python3 -m scraping scrape --headless --email lorenzmax098@gmail.com

dash:
	python3 -m scraping dash
