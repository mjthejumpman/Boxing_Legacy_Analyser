# import necessary packages
import requests
from bs4 import BeautifulSoup
import re

URL = "https://en.wikipedia.org/wiki/Joe_Louis"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

# extract name
name = soup.find(class_='mw-page-title-main').text
print(name)

# extract the infobox from the rest of the page elements
info_card = soup.find(class_='infobox')


# extract the table rows from the info card
tr = info_card.find_all('tr')

for row in tr:

    # extract alias
    alias_cell = row.find('td', class_='infobox-data nickname')

    if alias_cell:
        # check if the alias is inside a list
        first_li = alias_cell.find('li')
        if first_li:
            alias = first_li.get_text(strip=True)
        # otherwise, just take the raw value
        else:
            alias = alias_cell.get_text(strip=True)

        # strip quotations
        alias = alias.replace('"', '').replace("'", '').strip()

        print("Alias:", alias)

    th = row.find('th', class_='infobox-label')
    td = row.find('td', class_= 'infobox-data')
    # print(th,td)

    # extract the labels and values from each row
    if th and td:
        label = th.get_text(strip=True)
        value = td.get_text(strip=True)
        # print(label, ":", value)

        # put labels and values into a dictionary
        info_card_elements = {
            label : value
        }

        # print(info_card_elements)

        for k, v in info_card_elements.items():
            # extract stance
            try:
                if k == 'Stance':
                    Stance = v
                    print(Stance)
            except Exception as e:
                    print(f'Error extracting {k}: ',e)

            # extract d.o.b.
            try:
                if k == 'Born':
                    dob_string = v
                    iso_date_match = re.search(r'\((\d{4}-\d{2}-\d{2})\)', dob_string)
                    if iso_date_match:
                        iso_date = iso_date_match.group(1)
                        dob = iso_date
                        print(dob)
            except Exception as e:
                    print(f'Error extracting {k}: ',e)


            # extract height
            try:
                if k == 'Height':
                    height_string = v
                    # print("Height string:", height_string)

                    # search the data for cm
                    cm_match = re.search(r'(\d+)\s*cm', height_string)
                    if cm_match:
                        height_cm = int(cm_match.group(1))
                        print("Extracted height (cm):", height_cm)
                        continue

                    # search in metres and convert to cm
                    m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', height_string)
                    if m_match:
                        height_m = float(m_match.group(1))
                        height_cm = round(height_m * 100)
                        print("Extracted height (cm):", height_cm)
                        continue

                    # Unable to find value
                    print("Could not find height value.")
            except Exception as e:
                print(f'Error extracting {k}: ', e)

            # extract reach
            try:
                if k == 'Reach':
                    reach_string = v
                    # print("Reach string:", reach_string)

                    # search the data for cm
                    cm_match = re.search(r'(\d+)\s*cm', reach_string)
                    if cm_match:
                        height_cm = int(cm_match.group(1))
                        print("Extracted reach (cm):", height_cm)
                        continue

                    # search in metres and convert to cm
                    m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', reach_string)
                    if m_match:
                        height_m = float(m_match.group(1))
                        height_cm = round(height_m * 100)
                        print("Extracted reach (cm):", height_cm)
                        continue

                    # Unable to find value
                    print("Could not find reach value.")
            except Exception as e:
                print(f'Error extracting {k}: ', e)