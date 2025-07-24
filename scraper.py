# import general packages
from app import app
import requests
import re
from dateutil import parser

# import HTML parser
from bs4 import BeautifulSoup

# import database models
from models import db, Boxer, Fight, RankingMetrics

# import .env database credentials
from dotenv import load_dotenv
load_dotenv()

# setup logging function to check for errors whilst batch scraping
import logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')


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
    try:
        name = soup.find(class_='mw-page-title-main').text

        # insert name into data dictionary
        data['name'] = name
        logging.info("name insertion successful")
    except AttributeError as e:
        logging.error(f"Unable to extract name from page element. {e}")

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
                data['photo'] = complete_image_url
                logging.info(f"Extracted image URL: {complete_image_url}")
        except AttributeError as e:
            logging.error(f"Unable to extract photo cell from page element. {e}")

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

                logging.info("alias insertion successful")
        except AttributeError as e:
            logging.error(f"unable to extract {data.get('name')} alias from page element. {e}")

        th = row.find('th', class_='infobox-label')
        td = row.find('td', class_='infobox-data')

        # extract the labels and values from each row
        if th and td:
            label = th.get_text(strip=True)
            value = td.get_text(strip=True)

            # put labels and values into a dictionary
            info_card_elements = {
                label: value
            }


            for k, v in info_card_elements.items():
                # extract stance
                try:
                    if k == 'Stance':
                        stance = v

                        # insert stance into data dictionary
                        data['stance'] = stance
                        logging.info("stance insertion successful")
                except AttributeError as e:
                    logging.error(f"Unable to extract {data.get('name')} stance from page element. {e}")

                # extract d.o.b.
                try:
                    if k == 'Born':
                        dob_string = v
                        iso_date_match = re.search(r'\((\d{4}-\d{2}-\d{2})\)', dob_string)
                        if iso_date_match:
                            iso_date = iso_date_match.group(1)
                            dob = iso_date

                            # insert d.o.b. into data dictionary
                            data['birth_date'] = dob
                            logging.info("d.o.b. insertion successful")
                except AttributeError as e:
                    logging.error(f"Unable to extract {data.get('name')} date of birth from page element. {e}")

                # extract height
                try:
                    if k == 'Height':
                        height_string = v

                        # search the data for cm
                        cm_match = re.search(r'(\d+)\s*cm', height_string)
                        if cm_match:
                            height_cm = int(cm_match.group(1))

                            # insert Height into data dictionary
                            data['height_cm'] = height_cm
                            logging.info("height insertion successful")
                            continue

                        # search in metres and convert to cm
                        m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', height_string)
                        if m_match:
                            height_m = float(m_match.group(1))
                            height_cm = round(height_m * 100)

                            # insert Height into data dictionary
                            data['height_cm'] = height_cm
                            logging.info("height insertion successful")
                            continue
                except AttributeError as e:
                    logging.error(f"Unable to extract {data.get('name')} height from page element. {e}")

                # extract reach
                try:
                    if k == 'Reach':
                        reach_string = v

                        # search the data for cm
                        cm_match = re.search(r'(\d+)\s*cm', reach_string)
                        if cm_match:
                            reach_cm = int(cm_match.group(1))

                            # insert Reach into data dictionary
                            data['reach_cm'] = reach_cm
                            logging.info("reach insertion successful")
                            continue

                        # search in metres and convert to cm
                        m_match = re.search(r'(\d+(?:\.\d+)?)\s*m', reach_string)
                        if m_match:
                            reach_m = float(m_match.group(1))
                            reach_cm = round(reach_m * 100)

                            # insert Reach into data dictionary
                            data['reach_cm'] = reach_cm
                            logging.info("reach insertion successful")
                            continue
                except AttributeError as e:
                    logging.error(f"Unable to extract {data.get('name')} reach from page element. {e}")

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
        logging.error(f"Unable to locate fight table. {e}")

    # extract the headers and rows from the table
    try:
        fight_header_row = fight_table.find('tr')
        headers = [th.get_text(strip=True) for th in fight_header_row.find_all('th')]
        fight_data_rows = fight_table.find_all('tr')[1:]
    except AttributeError as e:
        logging.error(f"Unable to parse header and data rows from fight table. {e}")

    # construct matrix
    fight_matrix = []
    for row in fight_data_rows:
        cells = [td.get_text(strip=True) for td in row.find_all('td')]
        if len(cells) == len(headers):
            fight = dict(zip(headers, cells))
            fight_matrix.append(fight)


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

            # insert dates active from and until into data dictionary
            data['active_from'] = active_from
            data['active_until'] = active_until
            logging.info("active dates inserted successfully")
        else:
            print("None found.")
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} active to and until dates from page element. {e}")

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
            logging.error(f"Unable to define eras. {e}")

    # enter the oldest and newest dates from the fight list
    try:
        boxer_eras = define_eras(min(dates), max(dates))

        # insert eras into data dictionary
        data['era'] = boxer_eras
        logging.info("era insertion successful")
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} eras. {e}")

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
        logging.error(f"Unable to locate record table. {e}")

    # extract the headers and rows from the table
    try:
        record_header_row = record_table.find('tr')
    except AttributeError as e:
        logging.error(f"Unable to parse headers and data rows from record table. {e}")

    # extract number of fights, wins and losses
    try:
        number_of_fights = 0
        number_of_wins = 0

        for cell in record_header_row:
            text = cell.get_text(strip=True)

            if "fights" in text:
                number_of_fights = int(text.split()[0])

                # insert number_of_fights into data dictionary
                data['num_of_fights'] = number_of_fights

            if "wins" in text:
                number_of_wins = int(text.split()[0])

                # insert number_of_wins into data dictionary
                data['wins'] = number_of_wins

            if "losses" in text:
                number_of_losses = int(text.split()[0])

                # insert number_of_losses into data dictionary
                data['losses'] = number_of_losses
        logging.info("fight/win/loss insertion successful")
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} fights, wins and loss figures from page elements. {e}")

    # extract number of wins by KO, decision and DQ from data rows
    try:
        wins_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-yes2')]

        # wins by KO
        wins_by_ko = int(wins_by[0])

        # insert wins_by_ko into data dictionary
        data['wins_by_ko'] = wins_by_ko

        # wins by decision
        wins_by_decision = int(wins_by[1])

        # insert wins_by_decision into data dictionary
        data['wins_by_decision'] = wins_by_decision
        logging.info("win type insertion successful")

        # wins by DQ
        try:
            wins_by_dq = int(wins_by[2])

            # insert wins_by_dq into data dictionary
            data['wins_by_dq'] = wins_by_dq
        except IndexError:
            data['wins_by_dq'] = 0
            logging.info("wins_by_dq unavailable, defaulting to 0")

        else:
            wins_by_dq = None
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} wins by KO, decision and DQ from page elements. {e}")

    # extract number of losses by KO, decision and DQ from data rows
    try:
        losses_by = [td.get_text(strip=True) for td in record_table.find_all('td', class_='table-no2')]

        # losses by KO
        losses_by_ko = int(losses_by[0])

        # insert losses_by_ko into data dictionary
        data['losses_by_ko'] = losses_by_ko

        # losses by decision
        losses_by_decision = int(losses_by[1])

        # insert losses_by_decision into data dictionary
        data['losses_by_decision'] = losses_by_decision
        logging.info("loss type insertion successful")

        # losses by DQ
        try:
            losses_by_dq = int(losses_by[2])

            # insert losses_by_dq into data dictionary
            data['losses_by_dq'] = losses_by_dq
        except IndexError:
            data['losses_by_dq'] = 0
            logging.info("losses_by_dq unavailable, defaulting to 0")

        else:
            losses_by_dq = None
    except AttributeError as e:
        logging.error(f"Unable to extract {data.get('name')} losses by KO, decision and DQ  from page elements. {e}")

    # calculate the KO and win ratios
    try:
        win_ratio = round((number_of_wins / number_of_fights), 2)
        ko_ratio = round((wins_by_ko / number_of_wins), 2)

        # insert ko_ratio and win_ratio into data dictionary
        data['ko_ratio'] = ko_ratio
        data['win_ratio'] = win_ratio
        logging.info("ko and win ratio insertion successful")
    except AttributeError as e:
        logging.error(f"Unable to calculate {data.get('name')} KO and win ratios. {e}")

    return data, fight_matrix


# mapping of data to DB models and database insertion of boxer and ranking_metrics
# return error message to log file if boxer already in DB
def insert_boxer(data):
    with app.app_context():
        if not data.get('name'):
            logging.warning("No name available. Skipping boxer.")
            return

        existing = Boxer.query.filter_by(name=data['name']).first()
        if existing:
            logging.info(f"{data['name']} already in DB")
            return

        boxer = Boxer(
            name=data.get('name'),
            photo=data.get('photo'),
            alias=data.get('alias'),
            birth_date=data.get('birth_date'),
            stance=data.get('stance'),
            height_cm=data.get('height_cm'),
            reach_cm=data.get('reach_cm'),
            active_from=data.get('active_from'),
            active_to=data.get('active_until'),
            era=data.get('era'),
        )

        db.session.add(boxer)
        db.session.flush()

        ranking_metrics = RankingMetrics(
            boxer_id=boxer.id,
            ko_ratio=data.get('ko_ratio'),
            win_ratio=data.get('win_ratio'),
            num_of_fights=data.get('num_of_fights'),
            wins=data.get('wins'),
            wins_by_ko=data.get('wins_by_ko'),
            wins_by_decision=data.get('wins_by_decision'),
            wins_by_dq=data.get('wins_by_dq'),
            losses=data.get('losses'),
            losses_by_ko=data.get('losses_by_ko'),
            losses_by_decision=data.get('losses_by_decision'),
            losses_by_dq=data.get('losses_by_dq'),
        )


        db.session.add(ranking_metrics)
        db.session.commit()
        logging.info(f"Inserted {boxer.name} into DB")


# mapping the method section to adhere to db constraints
METHOD_MAPPING = {
    'KO': 'KO',
    'TKO': 'TKO',
    'RTD': 'TKO',
    'SD': 'Decision',
    'UD': 'Decision',
    'MD': 'Decision',
    'PTS': 'Decision',
    'DECISION': 'Decision',
    'TD': 'Decision',
    'DRAW': 'Draw',
    'TECHNICAL DRAW': 'Draw',
    'DQ': 'DQ',
    'NC': 'NC'
}

# database insertion into 'fights' table for each boxer
def insert_fights(fight_matrix, data):
    with app.app_context():
        boxer = Boxer.query.filter_by(name=data['name']).first()
        if not boxer:
            logging.warning(f"No boxer found for: {data['name']}")
            return

        # Not all ids available on first scraper pass, will be populated during second pass
        for fight_data in fight_matrix:
            opponent_name = fight_data.get('Opponent')
            winner_name = boxer.name if fight_data.get('Result') == "Win" else opponent_name

            # search for the id of boxer and opponent in the DB
            opponent_boxer = Boxer.query.filter_by(name=opponent_name).first()
            winner_boxer = Boxer.query.filter_by(name=winner_name).first()

            # normalise victory method to db constraints
            raw_method = fight_data.get('Type', '').strip().upper()
            method = METHOD_MAPPING.get(raw_method, None)

            fight = Fight(
                date=fight_data.get('Date'),
                rounds_completed=fight_data.get('Round, time') or fight_data.get('Round') or None,
                location=fight_data.get('Location'),
                title_fight=bool(fight_data.get('Notes', '').strip()),
                boxer_a_id=boxer.id,
                boxer_b_id=opponent_boxer.id if opponent_boxer else None,
                winner_id=winner_boxer.id if winner_boxer else None,
                opponent_name=opponent_name,
                winner_name=winner_name,
                method=method,
            )
            if method is None:
                logging.warning(f"invalid fight method '{raw_method}', for fight {fight_data.get('No.')}")

            if not opponent_boxer or not winner_boxer:
                logging.warning(f"unable to set all IDs for fight {fight_data.get('No.')}. Opponent: {opponent_name}, winner: {winner_name}")

            db.session.add(fight)

        db.session.commit()
        logging.info(f"Inserted {len(fight_matrix)} fights for {boxer.name}")



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

        data, fight_matrix = parse_data(html)
        insert_boxer(data)
        if fight_matrix:
            insert_fights(fight_matrix, data)


""" command line tool for testing purposes and insertion of fighters into DB
# s-mode for single URLs, b-mode for batch .txt files with URLs """
def main():
    mode = input("Choose mode - single (s) or batch (b): ").strip().lower()

    if mode == 's':
        url = input("Enter Wikipedia Boxer URL: ").strip()
        html = get_html_content(url)
        if html:
            data, fight_matrix = parse_data(html)
            insert_boxer(data)
            insert_fights(fight_matrix, data)
        print('operation complete')

    elif mode == 'b':
        print('initiating scrape')
        batch_scrape()
        print('scraping complete')


if __name__ == '__main__':
    main()