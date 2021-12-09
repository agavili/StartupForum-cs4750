from flask import Flask, redirect, url_for, flash, request, render_template, session
from flask import jsonify
from flask import Response
from flask import request
from flask_cors import CORS
from flask_bootstrap import Bootstrap
from flask_wtf import CSRFProtect
from forms import LoginForm, RegistrationForm, EditProfileForm, AddOrgSkillForm,\
    EditMajorForm, EditExpForm, EditMinorForm, AddClassForm, RemoveClassForm, CreateOrgForm, CreatePostForm, AddSkillForm, CreateJobForm, ScheduleInterviewForm
from data import skills_set
import datetime
import os
import requests
import hashlib
import pandas as pd
import random
#import pyodbc
import mysql.connector
from mysql.connector.constants import ClientFlag
from wtforms import Form, SelectField
from datetime import datetime
import json
import hashlib

# Application Setup
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)
SECRET_KEY = 'you-will-never-guess-12321312'
app.config['SECRET_KEY'] = SECRET_KEY
bootstrap = Bootstrap(app)
csrf = CSRFProtect()
csrf.init_app(app)

# DB Setup
cloud_sql_connection_name = 'prime-apricot-295200:us-east4:cs4750-startupforum'
db_socket_dir = '/cloudsql'
config = {
    'user': 'root',
    'password': 'password',
    'host': '10.74.80.3'
}
config['database'] = 'startup_forum'
config['port'] = 3306
cnxn = mysql.connector.connect(**config)


# Routes
@app.route('/login', methods=['GET', 'POST'])
def authenticate():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        salt = "5gz"
        db_password = password+salt
        h = hashlib.md5(db_password.encode())
        h = h.hexdigest()
        cursor = cnxn.cursor()  # initialize connection cursor
        cursor.execute(
            'SELECT * FROM User WHERE email = %s AND password = %s', (email, h,))
        account = cursor.fetchone()
        if account:
            flash(('Logged In'), 'success')
            session['loggedin'] = True
            session['id'] = account[0]  # user_id
            session['username'] = account[3]  # email
            return redirect((url_for('index')), code=302)
        else:
            flash(('Incorrect username/password!'), 'danger')
    return render_template('authenticate.html', title=('Sign In'), form=form)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('Logged Out', 'success')
    # Redirect to login page
    return redirect(url_for('authenticate'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/filtered', methods=['GET', 'POST'])
def index(filter_choice=1):
    request_id = filter_choice
    if 'loggedin' in session:
        userid = session['id']
        cursor = cnxn.cursor()
        special_filter = False
        sql_filtered = {}
        if(request.method == 'POST'):
            request_id = int(request.form['filter_choice'])
            special_filter = True
            sql_filtered = {
                1: 'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org ORDER BY datetime DESC',
                2: 'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org ORDER BY datetime ASC',
                3: 'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org WHERE Org.size >= 1 AND Org.size <= 10',
                4: 'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org WHERE Org.size >= 11 AND Org.size <= 50',
                5: 'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org WHERE Org.size >= 51',
            }
        if(request_id == 6):
            cursor.execute(
            'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org WHERE Org.org_title IN (SELECT Org.org_title FROM Org NATURAL JOIN Participate WHERE Participate.user_id = %s)', (userid,))
        elif(special_filter):
            cursor.execute(sql_filtered[request_id])
        else: 
            cursor.execute(
            'SELECT org_title, post_title, body, datetime FROM Forum_post NATURAL JOIN Org ORDER BY datetime DESC')
        forumposts = cursor.fetchall()
        cursor.execute(
            'SELECT * FROM Org NATURAL JOIN Participate WHERE Participate.user_id = %s', (userid,))
        organizations = cursor.fetchall()
        inOrganization = False
        if(len(organizations) > 0):
            inOrganization = True
        return render_template('index.html', title=('Home'), user_id = userid, username=session['username'], inOrg= inOrganization, forumposts=forumposts, request_id=request_id)
    return redirect(url_for('authenticate'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    msg = ''
    if form.validate_on_submit():
        cursor = cnxn.cursor(buffered=True)  # initialize connection cursor
        query = cursor.execute('SELECT * FROM User')
        count = cursor.fetchall()
        id_count = len(count)
        id_count += 1
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data
        salt = "5gz"
        db_password = password+salt
        h = hashlib.md5(db_password.encode())
        h = h.hexdigest()
        repeat_email = cursor.execute(
            'SELECT * FROM User WHERE email = %s', (email,))
        if repeat_email:
            flash('Email Already Taken', 'error')
            return redirect(url_for('register'))
        else:
            cursor.execute('INSERT INTO `User` (`user_id`, `first_name`, `last_name`, `email`, `password`) VALUES (%s, %s, %s, %s, %s)',
                           (id_count, first_name, last_name, email, h,))
            cnxn.commit()
            flash('Registration Successful', 'success')
            return redirect(url_for('authenticate'))
    return render_template('register.html', title=('Register'), form=form, msg=msg)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User WHERE user_id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        cursor.execute(
            'SELECT * FROM Participate JOIN Org WHERE user_id = %s AND Participate.org_id = Org.org_id', (session['id'],))
        orgs = cursor.fetchall()
        cursor.execute(
            'SELECT * FROM User_Experience JOIN Experience WHERE user_id = %s AND User_Experience.exp_id = Experience.exp_id', (session['id'],))
        exp = cursor.fetchall()
        cursor.execute(
            'SELECT * FROM Classes WHERE user_id = %s', (session['id'],))
        classes = cursor.fetchall()
        cursor.execute('SELECT * FROM Major WHERE user_id = %s',
                       (session['id'],))
        major = cursor.fetchone()
        cursor.execute('SELECT * FROM Minor WHERE user_id = %s',
                       (session['id'],))
        minor = cursor.fetchall()
        cursor.execute('SELECT * FROM Skills JOIN Learn WHERE user_id = %s AND Skills.skill_id = Learn.skill_id', (session['id'],))
        skills = cursor.fetchall()
        return render_template('profile.html', account=account, orgs=orgs, exp=exp, classes=classes, minor=minor, major=major, my_account=True, skills=skills)
    return redirect(url_for('authenticate'))


@app.route('/joblistings/', methods=['GET', 'POST'])
@app.route('/filtered-jobs', methods=['GET', 'POST'])
def getJobListings(filter_choice=1):
    request_id = filter_choice
    userid = session['id']
    cursor = cnxn.cursor()
    special_filter = False
    sql_filtered = {1: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id ORDER BY Advertised.job_id DESC'}
    if(request.method == 'POST'):
        request_id = int(request.form['filter_choice'])
        special_filter = True
        sql_filtered = {
            1: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id ORDER BY Advertised.job_id DESC',
            2: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id ORDER BY Advertised.job_id ASC',
            3: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id AND Org.size >= 1 AND Org.size <= 10 ORDER BY Advertised.job_id DESC',
            4: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id AND Org.size >= 11 AND Org.size <= 50 ORDER BY Advertised.job_id DESC',
            5: 'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id AND Org.size >= 51 ORDER BY Advertised.job_id DESC',
        }
    if(request_id == 6):
        cursor.execute(
        'SELECT org_title, Job.title, Job.description, Advertised.job_id FROM Job JOIN Advertised JOIN Org WHERE Job.job_id = Advertised.job_id AND Advertised.org_id = Org.org_id AND Org.org_title IN (SELECT Org.org_title FROM Org NATURAL JOIN Participate WHERE Participate.user_id = %s)', (userid,))
    else:
        cursor.execute(sql_filtered[request_id])
    joblistings = cursor.fetchall()
    return render_template('joblistings.html', title=('Job Listings'), joblistings=joblistings, request_id=request_id)


@app.route('/savedjobs', methods=['GET', 'POST'])
def getSavedJobs():
    cursor = cnxn.cursor()
    cursor.execute(
        'SELECT Saves_Job.job_id, Job.title, Job.description, Org.org_title, Saves_Job.timestamp FROM Job, Saves_Job, Advertised, Org WHERE Saves_Job.user_id = %s AND Saves_Job.job_id = Job.job_id AND Advertised.job_id = Saves_Job.job_id AND Org.org_id = Advertised.org_id', (session['id'],))
    savedJobs = cursor.fetchall()
    return render_template('savedJobs.html', title=('Your saved jobs'), savedJobs=savedJobs)


@app.route('/jobapps', methods=['GET', 'POST'])
def getJobApps():
    cursor = cnxn.cursor()
    cursor.execute(
        'SELECT Applications.job_id, Job.title, Job.description, Org.org_title, Applications.datetime, Applications.status FROM Job, Applications, Advertised, Org WHERE Applications.user_id = %s AND Applications.job_id = Job.job_id AND Advertised.job_id = Applications.job_id AND Org.org_id = Advertised.org_id',  (session['id'],))
    savedApplications = cursor.fetchall()
    return render_template('applications.html', title=('Your saved applications'), savedApplications=savedApplications)


@app.route('/profile/<id>', methods=['GET', 'POST'])
def view_profile(id):
    view_id = id
    if view_id == session['id']:
        my_account = True
    else:
        my_account = False
    cursor = cnxn.cursor(buffered=True)
    cursor.execute('SELECT * FROM User WHERE user_id = %s', (view_id,))
    account = cursor.fetchone()
    cursor.execute(
        'SELECT * FROM Participate JOIN Org WHERE user_id = %s AND Participate.org_id = Org.org_id', (view_id,))
    orgs = cursor.fetchall()
    cursor.execute(
        'SELECT * FROM User_Experience JOIN Experience WHERE user_id = %s AND User_Experience.exp_id = Experience.exp_id', (view_id,))
    exp = cursor.fetchall()
    cursor.execute('SELECT * FROM Classes WHERE user_id = %s', (view_id,))
    classes = cursor.fetchall()
    cursor.execute('SELECT * FROM Major WHERE user_id = %s', (view_id,))
    major = cursor.fetchone()
    cursor.execute('SELECT * FROM Minor WHERE user_id = %s', (view_id,))
    minor = cursor.fetchall()
    return render_template('profile.html', account=account, orgs=orgs, exp=exp, classes=classes, minor=minor, major=major, my_account=my_account)


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User_Experience WHERE user_id = %s',
                       (session['id'],))
        has_exp = cursor.fetchone()
        if 'loggedin' in session:
            form = EditProfileForm()
            if form.validate_on_submit():
                cursor.execute('SELECT * FROM User WHERE user_id = %s',
                               (session['id'],))
                account = cursor.fetchone()
                first_name = form.first_name.data
                last_name = form.last_name.data
                email = form.email.data
                password = form.password.data
                repeat_email = cursor.execute(
                    'SELECT * FROM User WHERE email = %s', (email,))
                if repeat_email:
                    msg = 'Email already taken!'
                    return redirect(url_for('edit_profile'))
                else:
                    cursor.execute('UPDATE User SET first_name = %s, last_name = %s, email = %s, password = %s WHERE User.`user_id` = %s', (
                        first_name, last_name, email, password, account[0],))
                    cnxn.commit()
                    return redirect(url_for('profile'))
        return render_template('edit_profile.html', title=('Edit Profile'), form=form, has_exp=has_exp)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/experience', methods=['GET', 'POST'])
def edit_experience():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User_Experience WHERE user_id = %s',
                       (session['id'],))
        exp = cursor.fetchone()
        form = EditExpForm()
        if form.validate_on_submit():
            year = form.year.data
            school = form.school.data
            cursor.execute('SELECT * FROM Experience')
            total = len(cursor.fetchall())
            total += 1
            if exp:
                cursor.execute(
                    'UPDATE Experience SET exp_id = %s, school = %s, year = %s WHERE `exp_id` = %s', (exp[0], school, year, exp[0],))
                cnxn.commit()
                flash('Experience Updated', 'success')
                return redirect(url_for('edit_profile'))
            else:
                cursor.execute(
                    'INSERT INTO Experience (`exp_id`, `school`, `year`) VALUES (%s, %s, %s)', (total, school, year,))
                cnxn.commit()
                cursor.execute(
                    'INSERT INTO User_Experience (`user_id`, `exp_id`) VALUES (%s, %s)', (session['id'], total,))
                cnxn.commit()
                flash('Experience Updated', 'success')
                return redirect(url_for('edit_profile'))
        return render_template('edit_experience.html', title=('Edit Experience'), form=form)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/major', methods=['GET', 'POST'])
def edit_major():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User WHERE user_id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM User_Experience WHERE user_id = %s',
                       (session['id'],))
        exp = cursor.fetchone()
        form = EditMajorForm()
        if form.validate_on_submit():
            cursor.execute('SELECT * FROM Major WHERE user_id = %s',
                           (session['id'],))
            has_maj = cursor.fetchone()
            major = form.major.data
            cursor.execute('SELECT * FROM Major')
            total = len(cursor.fetchall())
            major_id = total
            if has_maj:
                cursor.execute('UPDATE Major SET major_name = %s, major_id = %s WHERE user_id = %s AND exp_id = %s', (
                    major, major_id, account[0], exp[1],))
                cnxn.commit()
                flash('Major Updated', 'success')
                return redirect(url_for('edit_profile'))
            else:
                cursor.execute('INSERT INTO `Major` (`user_id`, `exp_id`, `major_id`, `major_name`) VALUES (%s, %s, %s, %s)', (
                    account[0], exp[1], major_id, major,))
                cnxn.commit()
                flash('Major Added', 'success')
                return redirect(url_for('edit_profile'))
        return render_template('edit_major.html', title=('Edit Major'), form=form)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/minor', methods=['GET', 'POST'])
def edit_minor():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User WHERE user_id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM User_Experience WHERE user_id = %s',
                       (session['id'],))
        exp = cursor.fetchone()
        form = EditMinorForm()
        if form.validate_on_submit():
            cursor.execute('SELECT * FROM Minor WHERE user_id = %s',
                           (session['id'],))
            has_min = cursor.fetchone()
            minor = form.minor.data
            cursor.execute('SELECT * FROM Minor')
            total = len(cursor.fetchall())
            minor_id = total
            if has_min:
                cursor.execute('UPDATE Minor SET minor_name = %s, minor_id = %s WHERE user_id = %s AND exp_id = %s', (
                    minor, minor_id, account[0], exp[1],))
                cnxn.commit()
                flash('Major Updated', 'success')
                return redirect(url_for('edit_profile'))
            else:
                cursor.execute('INSERT INTO `Minor` (`user_id`, `exp_id`, `minor_id`, `minor_name`) VALUES (%s, %s, %s, %s)', (
                    account[0], exp[1], minor_id, minor,))
                cnxn.commit()
                flash('Major Added', 'success')
                return redirect(url_for('edit_profile'))
        return render_template('edit_minor.html', title=('Edit Minor'), form=form)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/class', methods=['GET', 'POST'])
def add_class():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User WHERE user_id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM User_Experience')
        exp = len(cursor.fetchall())
        form = AddClassForm()
        if form.validate_on_submit():
            cursor.execute('SELECT * FROM Classes')
            classes = cursor.fetchall()
            course = form.course.data
            total = len(cursor.fetchall())
            major_id = total
            cursor.execute('INSERT INTO `Classes` (`user_id`, `exp_id`, `classes_id`, `classes_name`) VALUES (%s, %s, %s, %s)',
                           (account[0], total, total, course,))
            cnxn.commit()
            flash('Class Added', 'success')
            return redirect(url_for('add_class'))
        return render_template('add_class.html', title=('Add Class'), form=form)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/class/remove', methods=['GET', 'POST'])
def remove_class():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User WHERE user_id = %s',
                       (session['id'],))
        account = cursor.fetchone()
        form = RemoveClassForm()
        if form.validate_on_submit():
            class_name = form.course.data
            cursor.execute(
                'SELECT * FROM `Classes` WHERE user_id = %s AND classes_name = %s', (account[0], class_name,))
            exp = cursor.fetchone()
            cursor.execute(
                'DELETE FROM `Classes` WHERE user_id = %s AND exp_id = %s', (account[0], exp[1],))
            cnxn.commit()
            flash('Class Removed', 'success')
            return redirect(url_for('remove_class'))
        return render_template('remove_class.html', title=('Remove Class'), form=form)
    return redirect(url_for('authenticate'))

@app.route('/organization-info/<id>/skill', methods=['GET', 'POST'])
def add_org_skill(id):
    if 'loggedin' in session:
        org_id = id
        cursor = cnxn.cursor(buffered=True)
        form = AddOrgSkillForm()
        if form.validate_on_submit():
            skill = form.skill.data
            cursor.execute('SELECT * FROM Requires_Skill WHERE org_id = %s AND skill_id = %s', (org_id, skill,))
            dup_check = cursor.fetchone()
            if dup_check:
                flash('Cannot Add a Skill That is Already Required', 'error')
            else:
                cursor.execute('INSERT INTO `Requires_Skill` (`org_id`,`skill_id`) VALUES (%s, %s)',
                            (org_id, skill,))
                cnxn.commit()
                flash('Skill Added', 'success')
            return redirect(url_for('add_org_skill', id=org_id))
        return render_template('add_org_skill.html', title=('Add Required Skill'), form=form, id=org_id)
    return redirect(url_for('authenticate'))


@app.route('/profile/edit/skill', methods=['GET', 'POST'])
def add_skill():
    if 'loggedin' in session:
        cursor = cnxn.cursor(buffered=True)
        cursor.execute('SELECT * FROM User_Experience WHERE user_id = %s', (session['id'],))
        exp = cursor.fetchone()
        form = AddSkillForm()
        if form.validate_on_submit():
            skill = form.skill.data
            cursor.execute('INSERT INTO `Learn` (`user_id`, `exp_id`, `skill_id`) VALUES (%s, %s, %s)',
                           (exp[0], exp[1] ,skill))
            cnxn.commit()
            flash('Skill Added', 'success')
            return redirect(url_for('edit_profile'))
        return render_template('add_skill.html', title=('Add Skill'), form=form)
    return redirect(url_for('authenticate'))


@app.route('/organizations', methods=['GET', 'POST'])
def organizations():
    if 'loggedin' in session:
        cursor = cnxn.cursor()
        cursor.execute('SELECT * FROM Org')
        orglist = cursor.fetchall()
        return render_template('organizations.html', title=('Organization'), orglist=orglist)
    return redirect(url_for('authenticate'))


@app.route('/organizations/<id>/join', methods=['GET', 'POST'])
def joinorg(id):
    if 'loggedin' in session:
        org_id = id
        user_id = session['id']
        cursor = cnxn.cursor()
        cursor.execute(
            'INSERT INTO `Participate` (`org_id`, `user_id`) VALUES (%s, %s)', (org_id, user_id,))
        cnxn.commit()
        flash('You Have Joined The Organization', 'success')
        return redirect(url_for('organizations'))
    return redirect(url_for('authenticate'))


@app.route('/joblistings/savejob/<id>', methods=['GET', 'POST'])
def savejob(id):
    if 'loggedin' in session:
        job_id = id
        user_id = session['id']
        timestamp = datetime.now()
        cursor = cnxn.cursor()
        cursor.execute(
            "SELECT Count(*) FROM Saves_Job WHERE user_id=%s AND job_id=%s ", (user_id, job_id))
        jobSavedCount = cursor.fetchone()[0]
        if(jobSavedCount == 0):
            cursor.execute(
                'INSERT INTO `Saves_Job` (`user_id`, `timestamp`, `job_id`) VALUES (%s, %s, %s)', (user_id, timestamp, job_id))
            cnxn.commit()
            flash('Job Saved', 'success')
            return redirect(url_for('getSavedJobs'))
        else:
            found = 1
            flash('Job Has Already Been Saved', 'error')
            return redirect(url_for('getJobListings'))
    return redirect(url_for('authenticate'))

@app.route('/organization-info/<id>', methods=['GET', 'POST'])
def orginfo(id):
    if 'loggedin' in session:
        org_id = id
        cursor = cnxn.cursor()
        cursor.execute('SELECT * FROM Participate WHERE org_id = %s AND user_id = %s', (org_id, session['id'],))
        my_org = cursor.fetchone()
        cursor.execute('SELECT Advertised.org_id, Applications.user_id, User.first_name, User.last_name, User.email, Applications.job_id, Job.title, Job.description FROM Applications, Job, Advertised, User WHERE Advertised.org_id = %s AND Advertised.job_id = Applications.job_id AND Applications.status = "applied" AND Applications.user_id = User.user_id AND Applications.job_id = Job.job_id', (org_id,))
        appliedjobs = cursor.fetchall()
        #cursor.execute('SELECT Advertised.org_id, Applications.user_id, User.first_name, User.last_name, User.email, Applications.job_id, Job.title, Job.description FROM Applications, Job, Advertised, User, Interviews WHERE Advertised.org_id = %s AND Advertised.job_id = Applications.job_id AND Applications.status = "interviewing" AND Applications.user_id = User.user_id AND Applications.job_id = Job.job_id', (org_id,))
        cursor.execute('SELECT Advertised.org_id, Applications.user_id, User.first_name, User.last_name, User.email, Applications.job_id, Job.title, Job.description, Interviews.datetime, Interviews.location, Interviews.round FROM Applications, Job, Advertised, Interviews, User WHERE Advertised.org_id = %s AND Advertised.job_id = Applications.job_id AND Applications.status = "interviewing" AND Applications.user_id = User.user_id AND Applications.job_id = Job.job_id AND Interviews.job_id = Applications.job_id AND Interviews.user_id = Applications.user_id', (org_id,))
        interviewingjobs = cursor.fetchall()
        cursor.execute('SELECT * FROM Org WHERE org_id = %s',(org_id,))
        org_details = cursor.fetchone()
        cursor.execute('SELECT Skills.skill_title FROM Skills NATURAL JOIN Requires_Skill WHERE org_id = %s', (org_id,))
        skills = cursor.fetchall()
        return render_template('organization_info.html', title=('ORGANIZATION INFO'), appliedjobs=appliedjobs, org_details = org_details, interviewingjobs=interviewingjobs, my_org=my_org, skills=skills)
    return redirect(url_for('profile'))






@app.route('/scheduleInterview/<id>/<id_2>/<id_3>', methods = ['GET', 'POST'])
def scheduleinterview(id, id_2, id_3):
    if 'loggedin' in session:
        user_id = id
        job_id = id_2
        org_id = id_3
        status = "interviewing"
        cursor = cnxn.cursor()
        cursor.execute('SELECT * FROM User WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.execute('SELECT * FROM Job WHERE job_id = %s', (job_id,))
        job = cursor.fetchone()
        form = ScheduleInterviewForm()
        # cursor.execute('CREATE TRIGGER `setApplicationStatus` AFTER INSERT ON `Interviews` FOR EACH ROW BEGIN UPDATE Applications SET Applications.status = %s WHERE Applications.user_id = %s AND Applications.job_id = %s; END',
        # (status, user_id, job_id,))
        if form.validate_on_submit():
            location = form.location.data
            rounds= form.rounds.data
            datetime= form.datetime.data
            cursor = cnxn.cursor()
            cursor.execute('SELECT * FROM Interviews')
            total = len(cursor.fetchall())
            total += 1
            cursor.execute('INSERT INTO `Interviews` (`job_id`, `user_id`, `location`, `round`, `datetime`) VALUES (%s, %s, %s, %s, %s)',(job_id, user_id, location, rounds, datetime,))
            cnxn.commit()
            return redirect(url_for('orginfo', id = org_id))

        return render_template('schedule_interview.html', user=user, job=job, form=form)
    return redirect(url_for('orginfo'))


@app.route('/organizations/<id>/leave', methods=['GET', 'POST'])
def leaveorg(id):
    if 'loggedin' in session:
        org_id = id
        user_id = session['id']
        cursor = cnxn.cursor()
        cursor.execute(
            'DELETE FROM `Participate` WHERE `org_id` = %s AND `user_id`= %s', (org_id, user_id,))
        cnxn.commit()
        flash('You Have Left The Organization', 'success')
        return redirect(url_for('profile'))
    return redirect(url_for('authenticate'))

@app.route('/organizations/<id>/postjob/<orgname>', methods=['GET', 'POST'])
def postjob(id, orgname):
    if 'loggedin' in session:
        form = CreateJobForm()
        org_id = id
        if form.validate_on_submit():
            position = form.title.data
            description = form.description.data
            cursor = cnxn.cursor()
            cursor.execute('SELECT * FROM Job')
            total = len(cursor.fetchall())
            total += 1
            cursor.execute('INSERT INTO `Job` (`job_id`, `title`, `description`) VALUES (%s, %s, %s)',
                           (total, position, description,))
            cnxn.commit()
            cursor.reset()
            cursor.execute('INSERT INTO `Advertised` (`job_id`, `org_id`) VALUES (%s, %s)',
                           (total, org_id,))
            cnxn.commit()
            flash('Job Posted', 'success')
            return redirect(url_for('getJobListings'))
        return render_template('create_job.html', form=form, orgname= orgname)
    return redirect(url_for('authenticate'))

@app.route('/organizations/create', methods=['GET', 'POST'])
def createOrg():
    if 'loggedin' in session:
        form = CreateOrgForm()
        if form.validate_on_submit():
            title = form.title.data
            location = form.location.data
            industry = form.industry.data
            size = form.size.data
            description = form.description.data
            cursor = cnxn.cursor()
            cursor.execute('SELECT * FROM Org')
            total = len(cursor.fetchall())
            total += 1
            cursor.execute('INSERT INTO `Org` (`org_id`, `industry`, `location`, `size`, `description`, `org_title`) VALUES (%s, %s, %s, %s, %s, %s)',
                           (total, industry, location, size, description, title,))
            cnxn.commit()
            flash('Organization Created', 'success')
            return redirect(url_for('organizations'))
        return render_template('create_org.html', form=form)
    return redirect(url_for('authenticate'))


@app.route('/unsave/<id>', methods=['GET', 'POST'])
def unsavejob(id):
    if 'loggedin' in session:
        job_id = id
        user_id = session['id']
        timestamp = datetime.now()
        cursor = cnxn.cursor()
        cursor.execute(
            'DELETE FROM `Saves_Job` WHERE user_id = %s AND job_id = %s', (user_id, job_id))
        cnxn.commit()
        flash('Job Removed From Saved Jobs', 'success')
        return redirect(url_for('getSavedJobs'))
    return redirect(url_for('authenticate'))


@app.route('/withrawApp/<id>', methods=['GET', 'POST'])
def withdrawapp(id):
    if 'loggedin' in session:
        job_id = id
        user_id = session['id']
        timestamp = datetime.now()
        cursor = cnxn.cursor()
        cursor.execute(
            'DELETE FROM `Applications` WHERE user_id = %s AND job_id = %s', (user_id, job_id))
        cnxn.commit()
        flash('Application Withdrawn', 'success')
        return redirect(url_for('getJobApps'))
    return redirect(url_for('authenticate'))


@app.route('/withrawApp/<id>/<id_2>/<id_3>', methods=['GET', 'POST'])
def rejectapp(id, id_2, id_3):
    if 'loggedin' in session:
        user_id = id
        job_id = id_2
        org_id = id_3
        cursor = cnxn.cursor()
        cursor.execute(
            'DELETE FROM `Applications` WHERE user_id = %s AND job_id = %s', (user_id, job_id))
        cnxn.commit()
        flash('Application Rejected', 'success')
        return redirect(url_for('orginfo', id=org_id))
    return redirect(url_for('profile'))





@app.route('/postToForum/<user_id>', methods = ['GET', 'POST'])
def postToForum(user_id):
    if 'loggedin' in session:
        form = CreatePostForm()
        userid = session['id']
        cursor = cnxn.cursor()
        cursor.execute(
            'SELECT Org.org_title FROM Org NATURAL JOIN Participate WHERE Participate.user_id = %s', (userid,))
        org_dropdown_choices = [row[0] for row in cursor.fetchall()]
        form.dropdown.choices = list(enumerate(org_dropdown_choices))
        if form.validate_on_submit():
            title = form.title.data
            choices = dict(form.dropdown.choices)
            org_name = choices[int(form.dropdown.data)]
            cursor.execute('SELECT org_id FROM Org WHERE org_title = %s', (org_name.strip(),))
            org_id = cursor.fetchone()
            body = form.body.data
            current_date = datetime.now()
            cursor.reset()
            cursor.execute('INSERT INTO `Forum_post` (`org_id`, `post_title`, `body`, `datetime`) VALUES (%s, %s, %s, %s)',
                           (org_id[0], title, body, current_date,))
            cnxn.commit()
            return redirect(url_for('index'))
        return render_template('create_post.html', form=form)
    return redirect(url_for('authenticate'))

@app.route('/joblistings/applytojob/<id>', methods=['GET', 'POST'])
def applytojob(id):
    if 'loggedin' in session:
        job_id = id
        user_id = session['id']
        timestamp = datetime.now()
        status = 'applied'
        cursor = cnxn.cursor()
        cursor.execute(
            "SELECT Count(*) FROM Applications WHERE user_id=%s AND job_id=%s ", (user_id, job_id))
        appCount = cursor.fetchone()[0]
        if(appCount == 0):
            cursor.execute(
                'INSERT INTO `Applications` (`user_id`, `datetime`, `job_id`, `status`) VALUES (%s, %s, %s, %s)', (user_id, timestamp, job_id, status))
            cnxn.commit()
            return redirect(url_for('getJobApps'))
        else:
            appExists = 1
            return redirect(url_for('getJobListings'))
    return redirect(url_for('authenticate'))


@app.route('/upcominginterviews', methods=['GET', 'POST'])
def upcominginterviews():
    cursor = cnxn.cursor()
    cursor.execute(
        'SELECT Interviews.job_id, Job.title, Job.description, Org.org_title, Interviews.datetime, Interviews.location, Interviews.round FROM Job, Interviews, Advertised, Org WHERE Interviews.user_id = %s AND Interviews.job_id = Job.job_id AND Advertised.job_id = Interviews.job_id AND Org.org_id = Advertised.org_id', (session['id'],))
    interviews = cursor.fetchall()
    return render_template('upcoming_interviews.html', title=('My Interviews'), interviews=interviews)

@app.route('/interviewCompleted/<id>/<id_2>/<id_3>', methods=['GET', 'POST'])
def interviewdone(id, id_2, id_3):
    if 'loggedin' in session:
        user_id = id
        job_id = id_2
        org_id = id_3
        cursor = cnxn.cursor()
        cursor.execute(
                'DELETE FROM `Interviews` WHERE user_id = %s AND job_id = %s', (user_id, job_id))
        cnxn.commit()
        return redirect(url_for('orginfo', id=org_id))
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run(host="localhost", port=50000,
            debug=True)  # ssl_context='adhoc'
