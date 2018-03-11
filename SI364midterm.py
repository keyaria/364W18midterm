###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError,RadioField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
import requests
import datetime
import hashlib
import simplejson as json

import midterm_info
## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values

app.config['SECRET_KEY'] = 'alkj'
app.config["SQLALCHEMY_DATABASE_URI"] =  "postgres://keyariaw@localhost/keyariaw364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################
pub_key = midterm_info.pub_key
priv_key = midterm_info.priv_key



##################
##### MODELS #####
##################

class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    readscom = db.Column(db.String(10))


    def __repr__(self): 
        return "{} (ID: {})".format(self.name,self.id) 

class Character(db.Model):
    __tablename__="Character"
    id = db.Column(db.Integer, primary_key=True)
    char_name= db.Column(db.String(64))
    text = db.Column(db.String(280), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable = False)

    def __repr__(self): 
        return "{} (ID: {})".format(self.char_name,self.text,self.user_id,self.id)

class Char_info(db.Model):
    __tablename__="Char_info"
    id = db.Column(db.Integer, primary_key=True)
    descr = db.Column(db.String(1000), nullable = False)
    picture = db.Column(db.String(500), nullable = False)
    char_n = db.Column(db.Integer, db.ForeignKey('Character.id'), nullable=False)

    def __repr__(self): 
        return "{} (ID: {})".format(self.descr,self.picture,self.char_n,self.id) 
#class Comic(db.Model):
  #  id = db.Column(db.Integer, primary_key=True)
  #  name = db.Column(db.String(64))

  #  def __repr__(self): 
 #       return "{} (ID: {})".format(self.name,self.id) 

###################
###### FORMS ######
###################


class FavForm(FlaskForm):
    disname = StringField("Please Enter Name",validators=[Required()])
    favchar = StringField('Enter the name of one of your favorite Marvel Character', validators=[ Required(), Length(max=64) ])
    expla = StringField('Descibe why you like the character', validators=[ Required(), Length(max=280)])
    movorcom =   RadioField('Do you watch Marvel movies, read the comics, or both?', choices=[('M','Movies'),('C','Comics'),('B','Both')])
    submit = SubmitField()


class ComicForm(FlaskForm):
    comic = StringField("Please Enter Name of Comic",validators=[Required()])
    submit = SubmitField()

    def validate_comic(self,field):
        if len((field.data)) <= 1:
            raise ValidationError('Comic name must be longer')



#######################
###### VIEW FXNS ######
#######################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET', 'POST'])
def home():
   
    return render_template('base.html')



@app.route('/character', methods=['GET', 'POST'])
def get_character():
    form = FavForm()
    #form = FavForm(request.form)
    return render_template('character.html', form=form)
   # char_name = form.favchar.data
   # text = form.expla.data
  #  name = form.disname.data

@app.route('/ret_char',  methods=['POST', 'GET'])
def retriv_char():
    form = FavForm()
    empty_field = []
    name = request.args['disname']
    char_name = request.args['favchar']
    text = request.args['expla']
    readscom = request.args['movorcom']
    
    if name == '':
        empty_field.append('No name')
    if char_name == '':
        empty_field.append('No comic name')
    if text == '':
        empty_field.append('No explanation')

    print('here')
    if name and char_name and text: 
        name = request.args['disname']
        char_name = request.args['favchar']
        text = request.args['expla']
        #print(name)
       
        t = User.query.filter_by(name = name).first()
      
        if t:
            user = t
        else:
            user = User(name = name, readscom =readscom)
            db.session.add(user)
            db.session.commit()

        if Character.query.filter_by(char_name = char_name, text = text, user_id = user.id).first():
            flash('Character already there')
            return redirect(url_for('see_all_char'))
        else:
            charac = Character(char_name = char_name, text = text, user_id = user.id)
            db.session.add(charac)
            db.session.commit()
           ## flash('Character added')

            ## Gathering the character info with api
            url = "https://gateway.marvel.com:443/v1/public/characters"
            name = char_name
            ts = datetime.datetime.utcnow()

            has = hashlib.md5(str(ts).encode()+priv_key.encode()+pub_key.encode())

            param = {'name': name,'ts': ts, 'apikey': pub_key, 'hash': has.hexdigest() }
            search = (requests.get(url=url, params=param)).json()
            #print(search)
            results = search['data']['results']

            if Character.query.filter_by(char_name = char_name).count() > 1:
          
                  redirect(url_for('get_info'))
            else:
             
                picres = (results[0]['thumbnail']['path'] + '/portrait_incredible.' + results[0]['thumbnail']['extension'])
                cha_info = Char_info(descr = results[0]['description'], picture = picres, char_n = charac.id)
                db.session.add(cha_info)
                db.session.commit()
           


            return redirect(url_for('get_info'))

        
    flash(empty_field)

    
    #errors = [v for v in form.errors.values()]
    #if len(errors) > 0:
     #   flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return redirect(url_for('get_character'))

@app.route('/char_info')
def get_info():
    allof = Char_info.query.all()

    chac_in = [(i.descr, i.picture,Character.query.filter_by(id = i.id).first().char_name) for i in allof] 
    return render_template('character_info.html', allof = chac_in)

@app.route('/all_char')
def see_all_char():
    charac = Character.query.all()
   
    usertoo = [(t.char_name,t.text, User.query.filter_by(id=t.user_id).first().name,User.query.filter_by(id=t.user_id).first().readscom) for t in charac]
    
    return render_template('all_char.html', all_char = usertoo)

@app.route('/comic', methods=['GET','POST'])
def get_comic():


    form = ComicForm(request.form)
    comic_name = form.comic.data

    if request.method == 'POST' and form.validate_on_submit():
        comic_name = request.form['comic']
     
        url = "https://gateway.marvel.com:443/v1/public/series"
        
        ts = datetime.datetime.utcnow()
      
#priv_key=''
        has = hashlib.md5(str(ts).encode()+priv_key.encode()+pub_key.encode())

        param = {'title': comic_name,'ts': ts, 'apikey': pub_key, 'hash': has.hexdigest() }
        search = (requests.get(url=url, params=param)).json()
    
        results = search['data']['results']
        return render_template('comic.html', form=form, results=results)
   #return "Got results", redirect(url_for('get_comic')), 
        #return redirect(url_for('get_comic'), results=search['results'])

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
       flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('comic.html', form=form)

## Code to run the application...
if __name__== '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
