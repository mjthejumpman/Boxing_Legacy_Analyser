def resolve_opponents_and_winners():
    with app.app_context():
        fights = Fight.query.all()
        for fight in fights:
            if fight.opponent_name and not fight.boxer_b_id:
                opponent = Boxer.query.filter_by(name=fight.opponent_name).first()
                if opponent:
                    fight.boxer_b_id = opponent.id

            if fight.winner_name and not fight.winner_id:
                winner = Boxer.query.filter_by(name=fight.winner_name).first()
                if winner:
                    fight.winner_id = winner.id

        db.session.commit()
        print("Resolved opponents and winners.")
