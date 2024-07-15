# import needed libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# extracts the information of the reviewer
def extract_text_or_default(element, default="N/A"):
    return element.text.strip() if element else default

# extracts the information sibling text of the reviewer
def extract_sibling_text_or_default(element, default="N/A"):
    if element and element.find_next_sibling("td"):
        return element.find_next_sibling("td").text.strip()
    return default

# extracts the review
def extract_review_body(element):
    body_text = extract_text_or_default(element)
    if '|' in body_text:
        return body_text.split('|')[1].strip().strip('"')
    return body_text

# extracts the ratings
def extract_ratings(element):
    if element:
        stars = element.find_all("span", class_="star fill")
        if stars:
            return max(int(star.get_text()) for star in stars)
    return "N/A"

# date type conversion
def extract_review_info(review):
    review_dict = {}
    
    day_str = extract_text_or_default(review.find("time", itemprop="datePublished"))
    match = re.search(r"(\d+)(st|nd|rd|th) (\w+) (\d+)", day_str)
    if match:
        day, month_str, year = match.group(1), match.group(3), match.group(4)
        month = {
            "January": "01", "February": "02", "March": "03", "April": "04",
            "May": "05", "June": "06", "July": "07", "August": "08",
            "September": "09", "October": "10", "November": "11", "December": "12"
        }[month_str]
        review_dict["date"] = f"{day}/{month}/{year}"
    else:
        review_dict["date"] = day_str
    
    review_dict["name"] = extract_text_or_default(review.find("span", itemprop="name"))
    h3_text = extract_text_or_default(review.find("h3", class_="text_sub_header userStatusWrapper"))
    review_dict["country"] = h3_text.split(' (')[1].split(') ')[0] if '(' in h3_text else "N/A"
    review_dict["verification"] = extract_text_or_default(review.find("a", href="https://www.airlinequality.com/verified-reviews/"), "N/A")
    review_dict["review summary"] = extract_text_or_default(review.find("h2", class_="text_header"))
    review_dict["body"] = extract_review_body(review.find("div", itemprop="reviewBody"))
    review_dict["aircraft"] = extract_sibling_text_or_default(review.find("td", class_="aircraft"))
    review_dict["traveller type"] = extract_sibling_text_or_default(review.find("td", class_="type_of_traveller"))
    review_dict["seat type"] = extract_sibling_text_or_default(review.find("td", class_="cabin_flown"))
    review_dict["route"] = extract_sibling_text_or_default(review.find("td", class_="route"))
    review_dict["cabin staff service"] = extract_ratings(review.find("td", class_="cabin_staff_service").parent if review.find("td", class_="cabin_staff_service") else None)
    review_dict["food and beverages"] = extract_ratings(review.find("td", class_="food_and_beverages").parent if review.find("td", class_="food_and_beverages") else None)
    review_dict["value for money"] = extract_ratings(review.find("td", class_="value_for_money").parent if review.find("td", class_="value_for_money") else None)
    review_dict["recommend"] = extract_sibling_text_or_default(review.find("td", class_="recommended"))
    
    
    return review_dict

data = []
current_page = 1
proceed = True

while proceed:
    url = f"https://www.airlinequality.com/airline-reviews/british-airways/page/{current_page}/"
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'lxml')
    reviews = soup.find_all('article', itemprop="review")
    
    if not reviews:
        proceed = False
    else:
        for review in reviews:
            
            data.append(extract_review_info(review))
            
        current_page += 1
        print(current_page)
        

df = pd.DataFrame(data)
df.to_csv("ba_review.csv", index=False)
