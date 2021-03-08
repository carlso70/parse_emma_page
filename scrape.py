import json
import os
import re
from typing import Tuple, cast
import time


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

def accept_terms(driver) -> None:
    accept_button = driver.find_element_by_id('ctl00_mainContentArea_disclaimerContent_yesButton')
    accept_button.click()


# click_next_page selects the next button, returns true if clicked
def click_next_page(driver) -> bool:
    # find 'next' button to get the next list
    try:
        next_button = driver.find_element_by_class_name('next')
    except NoSuchElementException:
        print("no items on this page: ", driver.current_url)
        return False

    # Check if we can go to the next page or not
    attributes = next_button.get_attribute('class').split(" ")
    for attr in attributes:
        if attr == "disabled":
            return False

    # go to next page
    next_button.click()
    return True


def get_details_in_table(driver) -> list:
    details = []
    while True:
        time.sleep(0.5) # if there is no sleep the table doesn't load in time....very annoying
        for row in driver.find_elements_by_tag_name('tr'):
            row_data = row.find_elements_by_tag_name('td')
            if len(row_data) != 12:
                pass
            else:
                # the cusip is usally a link
                detail = {
                    "CUSIP": 'TODO',
                    "Principle Amount at Issuance ($)": row_data[1].text,
                    "Security Description": row_data[2].text,
                    "Coupon": row_data[3].text,
                    "Maturity Date": row_data[4].text,
                    "Price/Yield": row_data[5].text,
                    "Price": row_data[6].text,
                    "Yield": row_data[7].text,
                    "Fitch": row_data[8].text,
                    "KBRA": row_data[9].text,
                    "Moody's": row_data[10].text,
                    "S&P": row_data[11].text,
                }
                details.append(detail)

        if not click_next_page(driver):
            return details


def get_links_in_table(driver) -> list:
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

        if not click_next_page(driver):
            return links


def scrape_for_links_to_details(driver, links_to_issuers) -> list:
    links_to_details = []
    for index, link in enumerate(links_to_issuers):
        print("getting link to details on link", index, "of", len(links_to_issuers))
        driver.get(link)
        links_to_details.extend(get_links_in_table(driver))
        print("current detail link count", len(links_to_details))
    return links_to_details


def scrape_for_details(driver, links_to_details) -> list:
    details = []
    for index, link in enumerate(links_to_details):
        driver.get(link)
        print("getting details on link", index, "of", len(links_to_details))
        details.extend(get_details_in_table(driver))
        print("current detail count", len(details))


if __name__ == "__main__":
    LINKS_TO_ISSUERS_FILE = "links_to_issuers.json"
    LINKS_TO_ISSUERS_DETAILS_FILE = "links_to_issuers_details.json"
    DETAILS_JSON_FILE = "details.json"

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
            if links_to_issuers is None:
                raise FileNotFoundError
    except FileNotFoundError:
        print(f"no {LINKS_TO_ISSUERS_FILE}.....scraping website for new data")
        links_to_issuers = get_links_in_table(driver)

        # Save issuers links
        with open(LINKS_TO_ISSUERS_FILE, 'w') as issuer_link_file:
            json.dump(links_to_issuers, issuer_link_file, indent=4)

    driver.implicitly_wait(0.1)  # Implicit wait is needed for detail page

    # Go to each issuer's securities table
    links_to_details = []
    try:
        with open(LINKS_TO_ISSUERS_DETAILS_FILE) as json_file:
            links_to_details = json.load(json_file)
            if links_to_details is None:
                raise FileNotFoundError
    except FileNotFoundError:
        print(f"no {LINKS_TO_ISSUERS_DETAILS_FILE}...scraping website for new data")
        links_to_details = scrape_for_links_to_details(driver, links_to_issuers)
        # Save links to details
        with open(LINKS_TO_ISSUERS_DETAILS_FILE, 'w') as details_links_file:
            json.dump(links_to_details, details_links_file, indent=4)

    # Go inside each issue detail and get the data from the final table

    driver.implicitly_wait(1)
    details = []
    try:
        with open(DETAILS_JSON_FILE) as details_json_file:
            details = json.load(details_json_file)
            if details is None:
                raise FileNotFoundError
    except FileNotFoundError:
        print(f"no {DETAILS_JSON_FILE}...scraping website for new data")
        details = scrape_for_details(driver, links_to_details)
        # save details
        with open(DETAILS_JSON_FILE, 'w') as details_json_file:
            json.dump(details, details_json_file, indent=4)
