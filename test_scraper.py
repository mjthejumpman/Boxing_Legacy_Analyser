# import general packages
from app import app
import requests
import re
from dateutil import parser

# import HTML parser
from bs4 import BeautifulSoup

# import database models
from models import db, Boxer, Fight, Statline, RankingMetrics

# import .env database credentials
from dotenv import load_dotenv
load_dotenv()

# setup logging function to check for errors whilst batch scraping
import logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


# delete later
URL = "https://en.wikipedia.org/wiki/Joe_Louis"
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")


data = {}

"""
Sequence of extraction operations to pull data for the "boxers" database table
"""
# extract name
try:
    name = soup.find(class_='mw-page-title-main').text

    # insert name into data dictionary
    data['name'] = name
    print(f"\n{name}")
    logging.info("name insertion successful")
except AttributeError as e:
    logging.error("Unable to extract name from page element")

# extract the infobox from the rest of the page elements
info_card = soup.find(class_='infobox')


# extract the table rows from the info card
tr = info_card.find_all('tr')

for row in tr:

    # extract fighter photo
    try:
        photo_box = row.find('td', class_='infobox-image')
        photo_cell = photo_box.find('img', class_='mw-file-element') if photo_box else None
        if photo_cell:
            img_url = photo_cell.get('src')
            complete_image_url = "https:" + img_url
            data['photo_url'] = complete_image_url
            logging.info(f"Extracted image URL: {complete_image_url}")
        else:
            logging.warning("No photo URL found")
    except AttributeError as e:
        logging.error("Unable to extract photo cell from page element")

    # extract alias
    alias_cell = row.find('td', class_='infobox-data nickname')

    try:
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

            # insert alias into data dictionary
            data['alias'] = alias

            print("Alias:", alias)
            logging.info("alias insertion successful")
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} alias from page element")

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
                    print("Stance:", Stance)

                    # insert stance into data dictionary
                    data['stance'] = Stance
                    logging.info("stance insertion successful")
            except AttributeError as e:
                logging.error(f"Unable to extract {data.get('name')} stance from page element")

            # extract d.o.b.
            try:
                if k == 'Born':
                    dob_string = v
                    iso_date_match = re.search(r'\((\d{4}-\d{2}-\d{2})\)', dob_string)
                    if iso_date_match:
                        iso_date = iso_date_match.group(1)
                        dob = iso_date
                        print(dob)

                        # insert d.o.b. into data dictionary
                        data['birth_date'] = dob
                        logging.info("d.o.b. insertion successful")
            except AttributeError as e:
                logging.error(f"Unable to extract {data.get('name')} date of birth from page element")


            # extract height
            try:
                if k == 'Height':
                    height_string = v
                    # print("Height string:", height_string)

                    # search the data for cm
                    cm_match = re.search(r'(\d+)\s*cm', height_string)
                    if cm_match:
                        height_cm = int(cm_match.group(1))
                        print("Height (cm):", height_cm)

                        # insert Height into data dictionary
                        data['height_cm'] = height_cm
                        logging.info("height insertion successful")
                        continue

                    # search in metres and convert to cm
                    m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', height_string)
                    if m_match:
                        height_m = float(m_match.group(1))
                        height_cm = round(height_m * 100)
                        print("\nHeight (cm):", height_cm)

                        # insert Height into data dictionary
                        data['height_cm'] = height_cm
                        logging.info("height insertion successful")
                        continue

                    # Unable to find value
                    print("Could not find height value.")
            except AttributeError as e:
                logging.error(f"Unable to extract {data.get('name')} height from page element")

            # extract reach
            try:
                if k == 'Reach':
                    reach_string = v
                    # print("Reach string:", reach_string)

                    # search the data for cm
                    cm_match = re.search(r'(\d+)\s*cm', reach_string)
                    if cm_match:
                        reach_cm = int(cm_match.group(1))
                        print("Extracted reach (cm):", reach_cm)

                        # insert Reach into data dictionary
                        data['reach_cm'] = reach_cm
                        logging.info("reach insertion successful")
                        continue

                    # search in metres and convert to cm
                    m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', reach_string)
                    if m_match:
                        reach_m = float(m_match.group(1))
                        reach_cm = round(reach_m * 100)
                        print("Extracted reach (cm):", reach_cm)

                        # insert Reach into data dictionary
                        data['reach_cm'] = reach_cm
                        logging.info("reach insertion successful")
                        continue

                    # Unable to find value
                    print("Could not find reach value.")
            except AttributeError as e:
                logging.error(f"Unable to extract {data.get('name')} reach from page element")


"""
Sequence of extraction operations to continue to pull data for the "boxers" database table
and to pull data for the "fights" database table
"""

# extract the dates active from and active to from the wikitable
fight_table = None

# search for tables with header rows
try:
    for table in soup.find_all('table', class_='wikitable'):
        fight_header_row = table.find('tr')
        if not fight_header_row:
            continue

        headers = [th.get_text(strip=True) for th in fight_header_row.find_all('th')]

        # search for specific columns in the header. if present, extract that table
        if "Result" in headers and "Opponent" in headers and "Date" in headers:
            fight_table = table
            break
except AttributeError as e:
    logging.error(f"Unable to locate fight table")


# extract the headers and rows from the table
try:
    fight_header_row = fight_table.find('tr')
    headers = [th.get_text(strip=True) for th in fight_header_row.find_all('th')]
    # print("Headers:", headers)
    fight_data_rows = fight_table.find_all('tr')[1:]
except AttributeError as e:
    logging.error(f"Unable to parse header and data rows from fight table")

# construct matrix
fight_matrix = []
for row in fight_data_rows:
    cells = [td.get_text(strip=True) for td in row.find_all('td')]
    if len(cells) == len(headers):
        fight = dict(zip(headers, cells))
        fight_matrix.append(fight)

# for fight in fight_matrix:
#     print(fight)

# find and extract date first and last active
# helper function to parse dates of various formats
def parse_date(date_str):
    try:
        return parser.parse(date_str, fuzzy=True)
    except Exception:
        return None

# put all dates in a list
dates = []
for fight in fight_matrix:
    date_str = fight.get('Date')
    if date_str:
        dt = parse_date(date_str)
        if dt:
            dates.append(dt)

# extract the oldest and newest from the list
try:
    if dates:
        active_from = min(dates).strftime('%Y-%m-%d')
        active_until = max(dates).strftime('%Y-%m-%d')
        print(f'active from: {active_from}, to: {active_until}')

        # insert dates active from and until into data dictionary
        data['active_from'] = active_from
        data['active_until'] = active_until
        logging.info("active dates inserted successfully")
    else:
        print("None found.")
except AttributeError as e:
    logging.error(f"Unable to extract {data.get('name')} active to and until dates from page element")

# define eras that the fighter fought in
def define_eras(start_year, end_year):
    try:
        eras = []

        # extract year from dates
        extracted_start_year = start_year.strftime('%Y')
        extracted_end_year = end_year.strftime('%Y')

        # round the start and end decade down
        start = (int(extracted_start_year) // 10) * 10
        end = (int(extracted_end_year) // 10) * 10

        # increment the decade by ten and append to list
        current_decade = start
        while current_decade <= end:
            decade = str(current_decade)[-2:] + "s"
            eras.append(decade)
            current_decade += 10

        return eras
    except AttributeError as e:
        logging.error(f"Unable to define eras")

# enter the oldest and newest dates from the fight list
try:
    boxer_eras = define_eras(min(dates), max(dates))
    print("Eras: ", boxer_eras)

    # insert eras into data dictionary
    data['era'] = boxer_eras
    logging.info("era insertion successful")
except AttributeError as e:
    logging.error(f"Unable to extract {data.get('name')} eras")

"""
Sequence of extraction operations to pull data for the "ranking_metrics" database table
"""
record_table = None

# search for tables with header rows
try:
    for table in soup.find_all('table', class_='wikitable'):
        record_header_row = table.find('tr')
        if not record_header_row:
            continue

        headers = [th.get_text(strip=True) for th in record_header_row.find_all('th')]

        # search for specific record table columns in the header. if present, return True
        found_f = False
        found_w = False
        found_l = False

        for header in headers:
            if "fights" in header.lower():
                found_f = True
            if "wins" in header.lower():
                found_w = True
            if "losses" in header.lower():
                found_l = True

        # if all three columns present, table successfully identified
        if found_f and found_w and found_l:
            record_table = table
            break
except AttributeError as e:
    logging.error(f"Unable to locate record table")


# extract the headers and rows from the table
try:
    record_header_row = record_table.find('tr')
    record_headers = [th.get_text(strip=True) for th in record_header_row.find_all('th')]
    # print("Headers:", headers)
    data_rows = record_table.find_all('tr')[1:]
    # print("Data rows:", data_rows)
except AttributeError as e:
    logging.error(f"Unable to parse headers and data rows from record table")


# extract number of fights, wins and losses
try:
    number_of_fights = 0
    number_of_wins = 0

    for cell in record_header_row:
        text = cell.get_text(strip=True)

        if "fights" in text:
            number_of_fights = int(text.split()[0])
            print(text.split())
            print("number_of_fights :", number_of_fights)

            # insert number_of_fights into data dictionary
            data['num_of_fights'] = number_of_fights

        if "wins" in text:
            number_of_wins = int(text.split()[0])
            print("number_of_wins :", number_of_wins)

            # insert number_of_wins into data dictionary
            data['wins'] = number_of_wins

        if "losses" in text:
            number_of_losses = int(text.split()[0])
            print("number_of_losses :", number_of_losses)

            # insert number_of_losses into data dictionary
            data['losses'] = number_of_losses
    logging.info("fight/win/loss insertion successful")
except AttributeError as e:
    logging.error(f"Unable to extract {data.get('name')} fights, wins and loss figures from page elements")

# extract number of wins by KO, decision and DQ
try:
    wins_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-yes2')]
    # print('\n','wins by: ', wins_by)

    # wins by KO
    wins_by_ko = int(wins_by[0])
    print('\nwins by KO:', wins_by_ko)

    # insert wins_by_ko into data dictionary
    data['wins_by_ko'] = wins_by_ko

    # wins by decision
    wins_by_decision = int(wins_by[1])
    print('wins by decision:', wins_by_decision)

    # insert wins_by_decision into data dictionary
    data['wins_by_decision'] = wins_by_decision
    logging.info("win type insertion successful")

    # wins by DQ
    if wins_by[2]:
        wins_by_dq = int(wins_by[2])
        print('wins by DQ:', wins_by_dq)

        # insert wins_by_dq into data dictionary
        data['wins_by_dq'] = wins_by_dq

    else:
        wins_by_dq = None
        print('no wins by DQ')
except AttributeError as e:
    logging.error(f"Unable to extract {data.get('name')} wins by KO, decision and DQ from page elements")


# extract number of losses by KO, decision and DQ
try:
    losses_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-no2')]

    # wins by KO
    losses_by_ko = int(losses_by[0])
    print('\nlosses by KO:', losses_by_ko)

    # insert losses_by_ko into data dictionary
    data['losses_by_ko'] = losses_by_ko

    # wins by decision
    losses_by_decision = int(losses_by[1])
    print('losses by decision:',losses_by_decision)

    # insert losses_by_decision into data dictionary
    data['losses_by_decision'] = losses_by_decision
    logging.info("loss type insertion successful")

    # wins by DQ
    if losses_by[2]:
        losses_by_dq = int(losses_by[2])
        print('losses by DQ:', losses_by_dq)

        # insert losses_by_dq into data dictionary

        data['losses_by_dq'] = losses_by_dq

    else:
        losses_by_dq = None
        print('no losses by DQ')
except AttributeError as e:
    logging.error(f"Unable to extract {data.get('name')} losses by KO, decision and DQ  from page elements")


# calculate the KO and win ratios
try:
    win_ratio = round((number_of_wins / number_of_fights), 2)
    ko_ratio = round((wins_by_ko / number_of_wins), 2)
    print(f'\nwin ratio: {win_ratio} \nko ratio: {ko_ratio}')

    # insert ko_ratio and win_ratio into data dictionary
    data['ko_ratio'] = ko_ratio
    data['win_ratio'] = win_ratio
    logging.info("ko and win ratio insertion successful")
except AttributeError as e:
    logging.error(f"Unable to calculate {data.get('name')} KO and win ratios")

print(f'\n{data}')

# return data, fight_matrix