# Amazon Order History Web Scraper
Uses Selenium to simulate login and going through all the users orders. Saves the received data in a json
file for later evaluation.
  

# usage

When using a computer where you've not logged in before Amazon might requires a confirmation code from an email 
it has send to you. Therefore it can be necessary to login with your favorite browser before using that script. 
After logging in the first time there shouldn't be anymore email confirmations necessary.

Usage:
`python main --email abc@xy.z --password 123 [--headless]`

headless - is optional, if specified it starts an invisible crawler  