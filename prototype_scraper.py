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
# URL = "https://en.wikipedia.org/wiki/Joe_Louis"
# page = requests.get(URL)
# soup = BeautifulSoup(page.content, "html.parser")


# function to fetch the contents of wiki pages. return error message to log file if unsuccessful
def get_html_content(url):
    try:
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None


# parse the fetched data to retrieve information from the infobox and wiki tables
def parse_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    """
    Sequence of extraction operations to pull data for the "boxers" database table
    """
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

                print("Alias:", alias)
        except Exception as e:
            print(f'Error extracting {k}: ', e)

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


    # extract the dates active from and active to from the wikitable
    fight_table = None

    # search for tables with header rows
    for table in soup.find_all('table', class_='wikitable'):
        header_row = table.find('tr')
        if not header_row:
            continue

        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

        # search for specific columns in the header. if present, extract that table
        if "Result" in headers and "Opponent" in headers and "Date" in headers:
            fight_table = table
            break

    # test to see if fight table located
    if fight_table:
        print("fight table found")
        # print(fight_table.prettify())
    else:
        print("fight table not found.")


    # extract the headers and rows from the table
    header_row = fight_table.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
    # print("Headers:", headers)
    data_rows = fight_table.find_all('tr')[1:]

    # construct matrix
    fight_matrix = []
    for row in data_rows:
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
    if dates:
        active_from = min(dates).strftime('%Y-%m-%d')
        active_until = max(dates).strftime('%Y-%m-%d')
        print(f'active from: {active_from}, to: {active_until}')
    else:
        print("None found.")

    # define eras that the fighter fought in
    def define_eras(start_year, end_year):
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

    # enter the oldest and newest dates from the fight list
    boxer_eras = define_eras(min(dates), max(dates))
    print("Eras: ", boxer_eras)


    """
    Sequence of extraction operations to pull data for the "ranking_metrics" database table
    """
    record_table = None

    # search for tables with header rows
    for table in soup.find_all('table', class_='wikitable'):
        header_row = table.find('tr')
        if not header_row:
            continue

        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]

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


    # test to see if fight table located
    if record_table:
        print("record table found")
    else:
        print("record table not found.")


    # extract the headers and rows from the table
    header_row = record_table.find('tr')
    record_headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
    # print("Headers:", headers)
    data_rows = record_table.find_all('tr')[1:]
    # print("Data rows:", data_rows)

    # extract number of fights, wins and losses
    number_of_fights = 0
    number_of_wins = 0

    for cell in header_row:
        text = cell.get_text(strip=True)

        if "fights" in text:
            number_of_fights = int(text.split()[0])
            print("number_of_fights :", number_of_fights)

        if "wins" in text:
            number_of_wins = int(text.split()[0])
            print("number_of_wins :", number_of_wins)

        if "losses" in text:
            number_of_losses = int(text.split()[0])
            print("number_of_losses :", number_of_losses)


    # extract number of wins by KO, decision and DQ
    wins_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-yes2')]
    # print('\n','wins by: ', wins_by)

    # wins by KO
    wins_by_ko = int(wins_by[0])
    print('wins by KO:', wins_by_ko)

    # wins by decision
    wins_by_decision = int(wins_by[1])
    print('wins by decision:', wins_by_decision)

    # wins by DQ
    if wins_by[2]:
        wins_by_dq = int(wins_by[2])
        print('wins by DQ:', wins_by_dq)
    else:
        wins_by_dq = None
        print('no wins by DQ')

    # extract number of losses by KO, decision and DQ
    losses_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-no2')]
    print('\n','losses by: ', losses_by)

    # wins by KO
    losses_by_ko = int(losses_by[0])
    print('losses by KO:', losses_by_ko)

    # wins by decision
    losses_by_decision = int(losses_by[1])
    print('losses by decision:',losses_by_decision)

    # wins by DQ
    if losses_by[2]:
        losses_by_dq = int(losses_by[2])
        print('losses by DQ:', losses_by_dq)
    else:
        losses_by_dq = None
        print('no losses by DQ')

    # calculate the KO and win ratios
    win_ratio = round((number_of_wins / number_of_fights), 2)
    ko_ratio = round((wins_by_ko / number_of_wins), 2)
    print(f'\nwin ratio: {win_ratio} \nko ratio: {ko_ratio}')

    """
    Sequence of extraction operations to pull data for the "fights" database table
    """



# map the data to the DB models
def map_data(data):

    # 'boxer' table
    name = data.get('name')
    alias =
    birth_date =
    stance =
    height_cm =
    reach_cm =
    active_from =
    active_to =
    era =

    # 'fight' table
    date =
    rounds_scheduled =
    rounds_completed =
    method =
    location =
    title_fight =

    # 'ranking_metrics' table
    ko_ratio =
    win_ratio =
    num_of_fights =
    wins =
    wins_by_ko =
    wins_by_decision =
    wins_by_dq =
    losses =
    losses_by_ko =
    losses_by_decision =
    losses_by_dq =


    return {
        'name': name,
        'alias': alias,
        'birth_date': birth_date,
        'stance': stance,
        'height_cm': height_cm,
        'reach_cm': reach_cm,
        'active_from': active_from,
        'active_to': active_to,
        'era': era,
        'date': date,
        'rounds_scheduled': rounds_scheduled,
        'rounds_completed': rounds_completed,
        'method': method,
        'location': location,
        'title_fight': title_fight,
        'ko_ratio': ko_ratio,
        'win_ratio': win_ratio,
        'num_of_fights': num_of_fights,
        'wins': wins,
        'wins_by_ko': wins_by_ko,
        'wins_by_decision': wins_by_decision,
        'wins_by_dq': wins_by_dq,
        'losses': losses,
        'losses_by_ko': losses_by_ko,
        'losses_by_decision': losses_by_decision,
        'losses_by_dq': losses_by_dq,
    }


# database insertion. return error message to log file if boxer already in DB
def insert_boxer(map_data):
    with app.app_context():
        if not map_data.get('name'):
            logging.warning("No name available. Skipping boxer.")
            return

        existing = Boxer.query.filter_by(name=map_data['name']).first()
        if existing:
            logging.info(f"{map_data['name']} already in DB")
            return

        boxer = Boxer(
            name=map_data['name'],
            alias=map_data['alias'],
            birth_date=map_data['birth_date'],
            stance=map_data['stance'],
            height_cm=map_data['height_cm'],
            reach_cm=map_data['reach_cm'],
            active_from=map_data['active_from'],
            active_to=map_data['active_to'],
            era=map_data['era'],
        )

        fight = Fight(
            date=map_data['date'],
            rounds_scheduled=map_data['rounds_scheduled'],
            rounds_completed=map_data['rounds_completed'],
            method=map_data['method'],
            location=map_data['location'],
            title_fight=map_data['title_fight'],
        )

        ranking_metrics = RankingMetrics(
            ko_ratio=map_data['ko_ratio'],
            win_ratio=map_data['win_ratio'],
            num_of_fights=map_data['num_of_fights'],
            wins=map_data['wins'],
            wins_by_ko=map_data['wins_by_ko'],
            wins_by_decision=map_data['wins_by_decision'],
            wins_by_dq=map_data['wins_by_dq'],
            losses=map_data['losses'],
            losses_by_ko=map_data['losses_by_ko'],
            losses_by_decision=map_data['losses_by_decision'],
            losses_by_dq=map_data['losses_by_dq'],
        )

        db.session.add(boxer, fight, ranking_metrics)
        db.session.commit()
        logging.info(f"Inserted {boxer.name} into DB")


# batch URL scraper
def batch_scrape():
    try:
        with open("urls.txt", 'r') as f:
            url_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error("urls.txt file not found.")
        return

    if not url_list:
        logging.error("No URLs to process.")
        return

    for url in url_list:
        logging.info(f"Processing URL: {url}")

        html = get_html_content(url)
        if not html:
            continue

        parsed_data = parse_data(html)
        mapped_data = map_data(parsed_data)
        insert_boxer(mapped_data)



""" command line tool for testing purposes and insertion of fighters into DB
# s-mode for single URLs, b-mode for batch .txt files with URLs """

if __name__ == '__main__':
    mode = input("Choose mode - single (s) or batch (b): ").strip().lower()

    if mode == 's':
        url = input("Enter Wikipedia Boxer URL: ").strip()
        html = get_html_content(url)
        if html:
            parsed_data = parse_data(html)
            cleaned = map_data(parsed_data)
            insert_boxer(cleaned)
        print('operation complete')

    elif mode == 'b':
        batch_scrape()
        print('operation complete')