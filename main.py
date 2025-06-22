import os
import sys
from time import sleep
import json
import gzip
import requests

from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# ---

FROM_AIRPORT = os.getenv("FROM_AIRPORT", "SYD")
TO_AIRPORT = os.getenv("TO_AIRPORT", "SGN")
PASSENGER_COUNT = os.getenv("PASSENGER_COUNT", 2)
DATE_PAGE = os.getenv("DATE_PAGE", 7)
DATE_LABEL = os.getenv("DATE_LABEL", "25 February 2026, Wednesday")
EXPECTED_STOP_COUNT = os.getenv("EXPECTED_STOP_COUNT", 0)
EXPECTED_MILE_COUNT = os.getenv("EXPECTED_MILE_COUNT", 70000)
HEALTHCHECK_UUID = os.getenv("HEALTHCHECK_UUID")

# ---

options = webdriver.FirefoxOptions()
options.add_argument("-headless")
options.add_argument("--width=1920")
options.add_argument("--height=1080")

driver = webdriver.Firefox(options=options)
driver.get("https://www.delta.com/")
driver.implicitly_wait(10)

def terminate(result):
    print("TERMINATING")
    print(result)
    driver.close()
    sys.exit(0)

def response_interceptor(request, response):
    if "rm-offer-gql" not in request.path:
        return

    if response.status_code != 200:
        terminate("ERROR: response code is " + str(response.status_code))

    parsed = json.loads(gzip.decompress(response.body))
    offer_sets = parsed["data"]["gqlSearchOffers"]["gqlOffersSets"]

    for offer_set in offer_sets:
        for offer in offer_set["offers"]:
            try:
                stop_count = offer["additionalOfferProperties"]["totalTripStopCnt"]
                mile_count = offer["offerPricing"][0]["totalAmt"]["milesEquivalentPrice"]["mileCnt"]
            except:
                continue

            if mile_count == EXPECTED_MILE_COUNT and stop_count == EXPECTED_STOP_COUNT:
                try:
                    requests.get("https://hc-ping.com/" + HEALTHCHECK_UUID, timeout=10)
                except requests.RequestException as e:
                    print("Ping failed: %s" % e)
                terminate("POSITIVE")

    try:
        requests.get("https://hc-ping.com/" + HEALTHCHECK_UUID + "/fail", timeout=10)
    except requests.RequestException as e:
        print("Ping failed: %s" % e)
    terminate("NEGATIVE")

driver.response_interceptor = response_interceptor

# ---

def close_language_modal():
    try:
        lang_select_modal = driver.find_element(By.CSS_SELECTOR, ".lang-select-confrimation-modal")
        lang_btn = lang_select_modal.find_element(By.CSS_SELECTOR, "button")
        lang_btn.click()
    except:
        pass

def close_cookie_modal():
    try:
        driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
    except:
        pass

def set_airport(from_or_to, airport):
    driver.find_element(By.ID, from_or_to + "AirportName").click()
    search_input = driver.find_element(By.ID, "search_input")
    search_input.send_keys(airport)
    sleep(1)
    search_input.send_keys(Keys.RETURN)

def set_oneway():
    driver.find_element(By.ID, "selectTripType-val").click()
    driver.find_element(By.ID, "ui-list-selectTripType1").click()

def set_shop_with_miles():
    driver.find_element(By.XPATH, "//label[@for='shopWithMiles']").click()

def set_departure_date(page, aria_label):
    driver.find_element(By.ID, "input_departureDate_1").click()

    for i in range(page):
        driver.find_element(By.CSS_SELECTOR, ".dl-datepicker-1").click()

    driver.find_element(By.XPATH, "//a[@aria-label='" + aria_label + "']").click()
    driver.find_element(By.CSS_SELECTOR, ".donebutton").click()

def set_passengers(passengers):
    driver.find_element(By.ID, "passengers-val").click()
    driver.find_element(By.ID, "ui-list-passengers" + str(passengers-1)).click()

def open_adv_search():
    driver.find_element(By.ID, "adv-search").click()

def set_delta_one():
    driver.find_element(By.ID, "faresFor-val").click()
    driver.find_element(By.ID, "ui-list-faresFor5").click()

def submit_form():
    try:
        driver.find_element(By.ID, "btn-book-submit").click()
    except:
        driver.find_element(By.ID, "btnSubmit").click()

# ---

try:
    close_language_modal()
    close_cookie_modal()

    set_airport("from", FROM_AIRPORT)
    set_airport("to", TO_AIRPORT)
    set_oneway()
    set_shop_with_miles()
    set_departure_date(DATE_PAGE, DATE_LABEL)
    set_passengers(PASSENGER_COUNT)
    open_adv_search()
    set_delta_one()

    submit_form()
    sleep(60)
finally:
    try:
        driver.close()
    except:
        pass
