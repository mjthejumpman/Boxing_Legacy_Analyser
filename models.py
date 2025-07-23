from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Boxer(db.Model):
    __tablename__ = 'boxers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    photo = db.Column(db.Text, nullable=False)
    alias = db.Column(db.Text)
    birth_date = db.Column(db.Date)
    # nationality = db.Column(db.Text)
    stance = db.Column(db.Text)
    height_cm = db.Column(db.Integer)
    reach_cm = db.Column(db.Integer)
    # style = db.Column(db.Text)
    active_from = db.Column(db.Integer)
    active_to = db.Column(db.Integer)
    era = db.Column(db.Text)

    # table relationships
    fights_as_a = db.relationship('Fight', foreign_keys='Fight.boxer_a_id', back_populates='boxer_a')
    fights_as_b = db.relationship('Fight', foreign_keys='Fight.boxer_b_id', back_populates='boxer_b')
    wins = db.relationship('Fight', foreign_keys='Fight.winner_id', back_populates='winner')
    statlines = db.relationship('Statline', back_populates='boxer')
    ranking = db.relationship('RankingMetrics', uselist=False, back_populates='boxer')


class Fight(db.Model):
    __tablename__ = 'fights'

    id = db.Column(db.Integer, primary_key=True)
    boxer_a_id = db.Column(db.Integer, db.ForeignKey('boxers.id'))
    boxer_b_id = db.Column(db.Integer, db.ForeignKey('boxers.id'))
    winner_id = db.Column(db.Integer, db.ForeignKey('boxers.id'))
    date = db.Column(db.Date)
    rounds_completed = db.Column(db.Integer)
    method = db.Column(db.Text)
    location = db.Column(db.Text)
    title_fight = db.Column(db.Boolean)

    # table relationships
    boxer_a = db.relationship('Boxer', foreign_keys=[boxer_a_id], back_populates='fights_as_a')
    boxer_b = db.relationship('Boxer', foreign_keys=[boxer_b_id], back_populates='fights_as_b')
    winner = db.relationship('Boxer', foreign_keys=[winner_id], back_populates='wins')
    statlines = db.relationship('Statline', back_populates='fight')


class Statline(db.Model):
    __tablename__ = 'statlines'

    id = db.Column(db.Integer, primary_key=True)
    fight_id = db.Column(db.Integer, db.ForeignKey('fights.id'))
    boxer_id = db.Column(db.Integer, db.ForeignKey('boxers.id'))
    jabs_thrown = db.Column(db.Integer)
    jabs_landed = db.Column(db.Integer)
    power_thrown = db.Column(db.Integer)
    power_landed = db.Column(db.Integer)
    knockdowns = db.Column(db.Integer)
    punch_accuracy = db.Column(db.Float)
    opponent_accuracy = db.Column(db.Float)

    # table relationships
    fight = db.relationship('Fight', back_populates='statlines')
    boxer = db.relationship('Boxer', back_populates='statlines')


class RankingMetrics(db.Model):
    __tablename__ = 'ranking_metrics'

    boxer_id = db.Column(db.Integer, db.ForeignKey('boxers.id'), primary_key=True)
    adjusted_z_score = db.Column(db.Float)
    elo_rating = db.Column(db.Float)
    performance_score = db.Column(db.Float)
    ko_ratio = db.Column(db.Float)
    win_ratio = db.Column(db.Float)
    num_of_fights = db.Column(db.Float)
    wins = db.Column(db.Integer)
    wins_by_ko = db.Column(db.Integer)
    wins_by_decision = db.Column(db.Integer)
    wins_by_dq = db.Column(db.Integer)
    losses = db.Column(db.Integer)
    losses_by_ko = db.Column(db.Integer)
    losses_by_decision = db.Column(db.Integer)
    losses_by_dq = db.Column(db.Integer)


    # table relationships
    boxer = db.relationship('Boxer', back_populates='ranking')