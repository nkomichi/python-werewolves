from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from werewolves.auth import login_required
from werewolves.db import get_db

bp = Blueprint('game', __name__)


@bp.route('/')
def index():
    db = get_db()
    games = db.execute(
        'SELECT id, name, day, created, ended FROM game'
    )
    return render_template('game/index.html', games=games)


@bp.route('/<int:game_id>/', methods=('GET', 'POST'))
def game_current(game_id):
    if request.method == 'POST':
        error = None
        body = request.form['body']
        if not body:
            error = 'Body required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (body, author_id)'
                ' VALUES(?, ?)',
                (body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('game.game_current', game_id=game_id))


    db = get_db()
    posts = db.execute(
        'SELECT p.id, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('game/game.html', posts=posts)


@bp.route('/<int:game_id>/<int:day>/')
def game_history(game_id, day):
    db = get_db()
    game = db.execute(
        'SELECT id, name, day FROM game'
        ' WHERE id = ?',
        (game_id,)
    )

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO game (name)'
                ' VALUES (?);',
                (name)
            )
            game_id = db.execute(
                'SELECT id FROM game'
                ' WHERE rowid = last_insert_rowid();'
            ).fetchone()['id']
            db.commit()
            return redirect(url_for('game.game_current', game_id=game_id))

    return render_template('game/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))
    
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('game.index'))
    
    return render_template('game/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('game.index'))