import json
import os
import re
from typing import Tuple, cast

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.keys import Keys

# We use selenium to automate some web browser stuff that beautiful soup can't.
# That means we can click the javascript links on the website (ex: click accept terms and agreement stuff)


# TO GET GECKODRIVER.EXE yourself DOWNLOAD THIS THING HERE https://github.com/mozilla/geckodriver/releases and save it on your comp


# returns a tuple (x,y,z). Displaying x to y of z results
def parse_result_count(display_results_string: str) -> tuple:
    # Need to replace the ',' in numbers > 999 to parse correctly
    x = int(display_results_string.split(" ")[1].replace(',', ''))
    y = int(display_results_string.split(" ")[3].replace(',', ''))
    z = int(display_results_string.split(" ")[5].replace(',', ''))
    return (x, y, z)


def accept_terms(driver) -> None:
    accept_button = driver.find_element_by_id('ctl00_mainContentArea_disclaimerContent_yesButton')
    accept_button.click()


def get_links_in_table(driver, table_id) -> list:
    # get the details, this code pretty much the same as the issuers
    links = []
    while True:
        # find table on page and add links to each issuer
        for cell in driver.find_elements_by_css_selector('td'):
            try:
                link = cell.find_element_by_tag_name('a').get_attribute('href')
                links.append(link)
            except NoSuchElementException:
                pass

        # find 'next' button to get the next list
        try:
            next_button = driver.find_element_by_class_name('next')
        except NoSuchElementException:
            print("no items on this page: ", driver.current_url)
            return links

        # Check if we can go to the next page or not
        attributes = next_button.get_attribute('class').split(" ")
        for attr in attributes:
            if attr == "disabled":
                return links

        # go to next page
        next_button.click()


def scrape_for_links_to_details(driver, links_to_issuers) -> list:
    links_to_details = []
    for index, link in enumerate(links_to_issuers):
        print("getting details on link", index, "of", len(links_to_issuers))
        driver.get(link)
        links_to_details.extend(get_links_in_table(driver, ISSUER_PAGE_DETAIL_LINK_TABLE_ID))
        print("current detail count", len(links_to_details))
    return links_to_details


if __name__ == "__main__":
    MAIN_PAGE_ISSUER_LINK_TABLE_ID = 'lvIssuers'
    ISSUER_PAGE_DETAIL_LINK_TABLE_ID = 'lvIssues'

    LINKS_TO_ISSUERS_FILE = "links_to_issuers.json"
    LINKS_TO_ISSUERS_DETAILS_FILE = "links_to_issuers_details.json"

    driver = webdriver.Firefox(executable_path='.\geckodriver.exe')
    driver.maximize_window()  # maximize so all elements are clickable

    # Get website loaded
    driver.get("https://emma.msrb.org/IssuerHomePage/State?state=IL")

    # use selenium to accept terms and agreement
    accept_terms(driver)

    # gets links_to_issuers from file from previous run or scrape the site
    links_to_issuers = []
    try:
        with open(LINKS_TO_ISSUERS_FILE) as json_file:
            links_to_issuers = json.load(json_file)
    except FileNotFoundError:
        print(f"no {LINKS_TO_ISSUERS_FILE}.....scraping website for new data")
        links_to_issuers = get_links_in_table(driver, MAIN_PAGE_ISSUER_LINK_TABLE_ID)

        # Save issuers links
        with open(LINKS_TO_ISSUERS_FILE, 'w') as issuer_link_file:
            json.dump(links_to_issuers, issuer_link_file, indent=4)

    driver.implicitly_wait(0.1)  # Implicit wait is needed for detail page

    # Go to each issuer's securities table
    links_to_details = []
    try:
        with open(LINKS_TO_ISSUERS_DETAILS_FILE) as json_file:
            links_to_details = json.load(json_file)
    except FileNotFoundError:
        print(f"no {LINKS_TO_ISSUERS_DETAILS_FILE}...scraping website for new data")
        links_to_details = scrape_for_links_to_details(driver, links_to_issuers)
        # Save details
        with open(LINKS_TO_ISSUERS_DETAILS_FILE, 'w') as details_links_file:
            json.dump(links_to_details, details_links_file, indent=4)

    print(links_to_details)
    

