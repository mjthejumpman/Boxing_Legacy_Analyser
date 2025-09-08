# import app and db models
import app
from app.models import db, Boxer, Fight

# import progress bar and logging functionalities
from tqdm import tqdm
import logging

"""
During the fist pass of my scraper, the information to complete all of the opponent ID and winner fields was not available,
as some of the boxer IDs only become available once they are present in the DB. This is a function to resolve the missing
opponent and winner IDs in the "fights" table. 
"""
def resolve_fights():
    with app.app_context():

        # keep a log of unresolved winners and opponents
        opponent_log = open("db_resolver_unresolved_opponents.log", "w", encoding="utf-8")
        winner_log = open("db_resolver_unresolved_winners.log", "w", encoding="utf-8")

        fights = Fight.query.all()

        # loop through each fight in the table
        for i, fight in enumerate(tqdm(fights, desc="Resolving fights", unit="fight"), 1):

            # if the opponent name is present, and they are in the DB, enter their ID in the boxer_b_id column
            if fight.opponent_name and not fight.boxer_b_id:
                opponent = Boxer.query.filter_by(name=fight.opponent_name).first()
                if opponent:
                    fight.boxer_b_id = opponent.id
                # otherwise, add their name to the unresolved opponent log for future reference
                else:
                    opponent_log.write(fight.opponent_name + "\n")

            # if the winner name is present (and it isn't boxer_a), and they are in the DB
            # enter their ID in the boxer_b_id column
            if fight.winner_name and not fight.winner_id:
                winner = Boxer.query.filter_by(name=fight.winner_name).first()
                if winner:
                    fight.winner_id = winner.id
                # otherwise, add their name to the unresolved winner log for future reference
                else:
                    winner_log.write(fight.winner_name + "\n")

            # To mitigate progress loss and avoid a heavy final commit, save to db every 500 rows
            if i % 500 == 0:
                db.session.commit()
                logging.info(f"Committed {i} resolved fights...")


        db.session.commit()
        opponent_log.close()
        winner_log.close()
        print("Resolved opponents and winners in fights table\nunresolved items logged to files")
        logging.info("all resolutions committed")


if __name__ == "__main__":
    resolve_fights()