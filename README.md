# Amazon Order History Web Scraper
Uses Selenium to simulate login and going through all the users orders. Saves the received data in a json
file for later evaluation.

Currently only works for the german version of Amazon (amazon.de). For amazon.com users there is already a built in feature to export your data to a csv file.

# Usage

When using a device where you've not logged in before Amazon might require a confirmation code from an email 
it has send to you. Therefore it can be necessary to log into Amazon with your browser before using that script on a new device. 
After logging in the first time there shouldn't be anymore email confirmations necessary. The same applies if you
have two-factor authentication activated.

to install requirements:

`pip install -r requirements.txt`



Usage:

`python -m scraping --email abc@xy.z --password 123`

There are some optional parameters available, `python -m scraping --help` shows a description for each of them.
