from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from app.models import Boxer, db, RankingMetrics, Fight
from sqlalchemy import text, or_
from app.logic import elo_winner

main = Blueprint('main', __name__)

# fighter selection screen
@main.route('/')
def select():
    boxers = Boxer.query.order_by(Boxer.name).all()
    return render_template('select.html', boxers=boxers)

# SCRAPPED: transition page with animated elements and sound effect
@main.route('/transition', methods = ['POST'])
def transition():
    return render_template('transition.html')

# fight results screen
@main.route('/results', methods = ['GET', 'POST'])
def results():

    # retrieve fighter IDs from the select.html form
    boxer_a_id = request.form.get('boxer_a', type=int)
    boxer_b_id = request.form.get('boxer_b', type=int)

    # fetch the Boxer objects
    boxer_a = Boxer.query.get(boxer_a_id)
    boxer_b = Boxer.query.get(boxer_b_id)

    winner_id, elo_prob, win_type, elo_differential, prob_ko = elo_winner(boxer_a, boxer_b)

    winner_name = boxer_a.name if winner_id == boxer_a.id else boxer_b.name

    return render_template('results.html', boxer_a=boxer_a, boxer_b=boxer_b, boxer_a_id=boxer_a_id,
                           boxer_b_id=boxer_b_id, winner_name = winner_name, prob_ko = prob_ko, win_type = win_type,
                           elo_differential = elo_differential, percentage_victory = round(elo_prob * 100, 1))


# GET API to return a JSON object with fighter details for use with JavaScript
@main.route('/api/boxer/<boxer_id>', methods=['GET'])
def get_boxer(boxer_id):
    # query the database for the boxer id
    boxer = Boxer.query.get(boxer_id)
    if not boxer:
        return jsonify({'error': 'Boxer not found'}), 404
    ranking = RankingMetrics.query.get(boxer_id)
    fights = Fight.query.filter(or_(Fight.boxer_a_id == boxer_id, Fight.boxer_b_id == boxer_id)).all()

    # convert the fights into a list of dictionaries
    fight_data = []
    for fight in fights:
        fight_data.append({
            'id': fight.id,
            'boxer_a_id': fight.boxer_a_id,
            'boxer_b_id': fight.boxer_b_id,
            'winner_id': fight.winner_id,
            'date': fight.date.isoformat() if fight.date else None,
            'rounds_completed': fight.rounds_completed,
            'method': fight.method,
            'location': fight.location,
            'title_fight': fight.title_fight,
        })

    # return JSON object with fighter details and the fight_data list for the JavaScript function to parse
    return jsonify({
        'name': boxer.name,
        'alias': boxer.alias,
        'photo': boxer.photo,
        'height_cm': boxer.height_cm,
        'reach_cm': boxer.reach_cm,
        'stance': boxer.stance,
        'adjusted_z_score': ranking.adjusted_z_score if ranking else None,
        'elo_rating': ranking.elo_rating if ranking else None,
        'performance_score': ranking.performance_score if ranking else None,
        'ko_ratio': ranking.ko_ratio if ranking else None,
        'win_ratio': ranking.win_ratio if ranking else None,
        'num_of_fights': ranking.num_of_fights if ranking else None,
        'wins': ranking.wins if ranking else None,
        'wins_by_ko': ranking.wins_by_ko if ranking else None,
        'wins_by_decision': ranking.wins_by_decision if ranking else None,
        'wins_by_dq': ranking.wins_by_dq if ranking else None,
        'losses': ranking.losses if ranking else None,
        'losses_by_ko': ranking.losses_by_ko if ranking else None,
        'losses_by_decision': ranking.losses_by_decision if ranking else None,
        'losses_by_dq': ranking.losses_by_dq if ranking else None,
        'eras': boxer.era if ranking else None,
        'fights': fight_data,
    })


# test to confirm Supabase connection is functional
@main.route('/test-db')
def test_db():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()
        return f"Database connection successful: {result}"
    except Exception as e:
        return f"Database connection failed: {e}"