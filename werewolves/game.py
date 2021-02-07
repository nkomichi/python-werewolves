import re
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werewolves.auth import login_required
from werewolves.db import get_db

bp = Blueprint('game', __name__)

GM_NAME = 'GameMaster'
ROLE_GM = 0

@bp.route('/')
def index():
    db = get_db()
    games = db.execute(
        'SELECT id, title, day, created, ended FROM game'
    )
    return render_template('game/index.html', games=games)


def post_message(game_id, body):
    game = get_game(game_id)
    db = get_db()
    latest_post = db.execute(
        'SELECT number FROM post WHERE game_id = ? AND day = ?'
        ' ORDER BY number DESC LIMIT 1',
        (game_id, game['day'])
    ).fetchone()
    if latest_post:
        post_number = latest_post['number'] + 1
    else:
        post_number = 1
    try:
        db.execute(
            'INSERT INTO post (game_id, day, number, author_id, body)'
            ' VALUES(?, ?, ?, ?, ?)',
            (game_id, game['day'], post_number, g.user['id'], body)
        )
        db.commit()
    except:
        return False
    return True


def get_posts(game_id, day):
    posts = get_db().execute(
        'SELECT number, name author, body, created'
        ' FROM post JOIN play ON post.game_id = play.game_id AND post.author_id = play.user_id'
        ' WHERE post.game_id = ? AND day = ?'
        ' ORDER BY created',
        (game_id, day)
    ).fetchall()
    return posts


@bp.route('/<int:game_id>/', methods=('GET', 'POST'))
def current(game_id):
    if request.method == 'POST':
        error = None
        body = request.form['body']
        if not body:
            error = 'Body required.'
        if error is not None:
            flash(error)
        elif body[:1] == '/':
            if body[:2] == '//':
                post_message(game_id=game_id, body=body[1:])
            else:
                command = body.split()[0]
                if command == '/':
                    flash(f"Invalid command: {command}")
                elif command in '/join':
                    if len(body.split()) > 1:
                        name = body.split()[1]
                    else:
                        name = None
                    command_join(game_id, name)
                elif command in '/next':
                    command_next(game_id)
                else:
                    flash(f"Invalid command: {command}")
            return redirect(url_for('game.current', game_id=game_id))
        else:
            post_message(game_id=game_id, body=body)
            return redirect(url_for('game.current', game_id=game_id))

    game = get_game(game_id)
    posts = get_posts(game_id, game['day'])
    return render_template('game/game.html', game=game, posts=posts)


@bp.route('/<int:game_id>/<int:day>/')
def history(game_id, day):
    db = get_db()
    game = db.execute(
        'SELECT id, title, day FROM game'
        ' WHERE id = ?',
        (game_id,)
    )
    posts = get_posts(game_id, day)
    return render_template('game/game.html', game=game, posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        error = None

        if not title:
            error = 'Titile is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO game (title)'
                ' VALUES (?);',
                (title,)
            )
            game_id = db.execute(
                'SELECT id FROM game'
                ' WHERE rowid = last_insert_rowid();'
            ).fetchone()['id']
            db.execute(
                'INSERT INTO play (user_id, game_id, name, role)'
                ' VALUES (?, ?, ?, ?)',
                (g.user['id'], game_id, GM_NAME, ROLE_GM)
            )
            db.commit()
            return redirect(url_for('game.current', game_id=game_id))

    return render_template('game/create.html')



def get_game(game_id):
    """ゲーム情報を取得する"""
    game = get_db().execute(
        'SELECT id, title, day, humans, wolves FROM game WHERE id = ?', (game_id,)
    ).fetchone()
    return game


def is_game_finished(game):
    """ゲームの勝敗を判定する"""
    winner = None
    if game['wolves'] <= 0:
        winner = 'humans'
    if game['wolves'] >= game['humans']:
        winner = 'wolves'
    return winner


def command_join(game_id, name=None):
    """ゲームに参加する"""
    error = None
    game = get_game(game_id)
    if game['day'] != 0:
        error = 'You can join only on day 0.'
    db = get_db()
    players = db.execute(
        'SELECT user_id, name FROM play WHERE game_id = ?', (game_id,)
    ).fetchall()
    ids = [x['user_id'] for x in players]
    names = [x['name'] for x in players]
    if g.user['id'] in ids:
        error = 'You have already joined this game.'
    if name in names:
        error = f"Name {name} is already used."

    if error is not None:
        flash(error)
        return False
    else:
        try:
            db.execute(
                'INSERT INTO play (user_id, game_id, name)'
                ' VALUES (?, ?, ?)',
                (g.user['id'], game_id, name)
            )
            db.commit()
        except:
            return False
        return True


def command_next(game_id):
    """GMコマンド　ゲームのフェーズを進行させる"""
    pass

def proceed_day(game_id):
    """日を進める"""
    pass
