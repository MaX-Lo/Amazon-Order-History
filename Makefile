install:
	pip3 install -r requirements.txt

type_check:
	python3 -m mypy scraping

lint:
	python3 -m pylint scraping

scrape:
	python3 -m scraping scrape --email abc@de.xy

headless:
	python3 -m scraping scrape --headless --email abc@de.xy

dash:
	python3 -m scraping dash

cli:
	python3 -m scraping cli