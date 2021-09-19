from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
from oauth2client import file, client, tools
from httplib2 import Http
from werkzeug.utils import secure_filename
import os
from flask import Flask, flash, request, redirect, url_for, render_template, session
from flask_session import Session
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
# from pydrive.auth import GoogleAuth
# from pydrive.drive import GoogleDrive
# gauth = GoogleAuth()
# gauth.LocalWebserverAuth()
# drive = GoogleDrive(gauth)

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/drive']

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
sess = Session()
app.config["UPLOAD_FOLDER"] = "images/"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024
creds = None


@app.route('/')
def index():
    return render_template('index.html', videos=['akun_1.mp4', 'video2.mp4'])


def uploadFile(path: str, filename: str, service):
    print(path)
    file_metadata = {
        'name': filename,
        'parents': ['1IOJ74hWCW0NmFKA2s9MAbtkn6878qupQ'],
        'mimeType': 'image/jpeg',
    }
    media = MediaFileUpload(path, mimetype='image/jpeg', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: ' + file.get('id'))


def authenticate():
    global creds
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)


@app.route('/upload-image', methods=['GET', 'POST'])
def upload_file():
    global creds, drive
    if request.method == 'GET':
        return redirect('/')
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        if request.files:
            print(request.files)
            image = request.files['file']
            # if user does not select file, browser also submit a empty part without filename
            if image.filename == '':
                flash('No selected file')
                return redirect(request.url)
            video = request.form.get('videos')

            if image and allowed_file(image.filename):
                image.save(image.filename)
            print(f"{image.filename} saved")
            service = authenticate()
            # Call the Drive v3 API
            # results = service.files().list(
            #     pageSize=10, fields="nextPageToken, files(id, name)").execute()
            # image.save(fp)
            combined = image.filename[:image.filename.rindex(
                '.')] + '__' + video + '__' + image.filename[image.filename.rindex('.'):]
            uploadFile(image.filename, combined, service)
            print(f"{image.filename} uploaded")
        return redirect(url_for('.beauty', video=combined[:combined.rindex('.')] + 'mp4'))


@app.route('/beauty', methods=['GET'])
def beauty(video='name.mp4'):
    service = authenticate()

    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    file_id = '1nuD-rTSN3urej50DYZqUIc1Yh6nAeX16'
    for item in items:
        if item['name'] == video:
            file_id = item['id']

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    with open("static/output.mp4", "wb") as f:
        f.write(fh.getbuffer())
    return render_template('video.html', video='download.mp4')


if __name__ == "__main__":
    # Quick test configuration. Please use proper Flask configuration options
    # in production settings, and use a separate file or environment variables
    # to manage the secret key!
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)

    app.debug = True
    app.run()
