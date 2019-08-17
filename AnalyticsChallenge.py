from random import randint
import os
from time import strftime
from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, validators,  FileField
from flask_wtf.file import FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from werkzeug.datastructures import CombinedMultiDict
import pandas as pd
from sklearn.metrics import accuracy_score

# App configurations
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'

UPLOAD_FOLDER = "/Users/balu/Work/FlaskPage/uploaded_files/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# create form class
class UploadForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    psid = TextField("PS_ID:", validators=[validators.required(), validators.regexp('[0-9]{7}')])
    myfile = FileField("TestSet File", validators=[FileAllowed(['csv']), FileRequired()])

# Get the accuracy score
def get_accuracy(testfile):
    # Load reference sample
    df_ref = pd.read_csv('ref_sample.csv')
    ref_values = df_ref.VALUE
    
    # Loading test sample
    df_sample = pd.read_csv(testfile)
    sample_values = df_sample.VALUE
    
    # Check number of rows are equal
    if (df_ref.shape[0] == df_sample.shape[0]):
        pred_accuracy = accuracy_score(ref_values, sample_values)
        return round(pred_accuracy*100, 2)
    else:
        return("Mismatch in number of entries")

# Get timestamp
def get_time():
    time = strftime("%Y-%m-%dT%H:%M")
    return time

# Write log to file
def write_to_disk(name, psid, filename, accuracy_score):
    data = open('webform_file.csv', 'a')
    timestamp = get_time()
    # data.write('DateStamp={}, Name={}, psid={}, filename={},  Accuracy={}\n'.format(timestamp, name, psid, filename, accuracy_score))
    data.write('{}, {}, {}, {}, {}\n'.format(timestamp, name, psid, filename, accuracy_score))
    data.close()

# Get Top10 Count
def get_top10():
    df = pd.read_csv('webform_file.csv')
    df = (df
          .sort_values('Accuracy',ascending=False)
          .drop_duplicates(['PS_ID']))
    df = df[['PS_ID', 'Accuracy']]
    df = df[0:10].reset_index(drop=True)
    df.index = df.index + 1
    return df


@app.route("/", methods=['GET', 'POST'])
def hello():

    form = UploadForm(CombinedMultiDict((request.files, request.form)))
    top10 = get_top10()
    if request.method == 'POST':
        if form.validate():
            # Get the values
            name=request.form['name']
            psid=request.form['psid']
            myfile = request.files['myfile']
            
            # Get file name
            filename = secure_filename(myfile.filename)
            
            # Saving the file and log
            testfile_path = os.path.join(app.config['UPLOAD_FOLDER'], 
                            get_time() + '_' + psid + '_' + filename) 
            myfile.save(testfile_path)
            
            # Get accuracy score
            accuracy_score = get_accuracy(testfile_path)
            
            # Saving the file and log
            # myfile.save(os.path.join(app.config['UPLOAD_FOLDER'], 
            #                 get_time() + '_' + psid + '_' + filename))
            
            write_to_disk(name, psid, filename, accuracy_score)
            
            # get top10 values
            top10 = get_top10()
            
            # Send output message to Screen
            flash('Hello: {} {} your accuracy is: {}'
                  .format(name, psid, accuracy_score))

        else:
            flash('Error: All Fields are Required. Also, please check whether psid and file extension are correct')

    return render_template('index.html', form=form, top10=top10)
   
    # tables=[top10.to_html(classes='data', header="true")])

if __name__ == "__main__":
    app.run()
