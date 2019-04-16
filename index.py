from flask import request, redirect, url_for
import json
from google.oauth2 import service_account
from httplib2 import Http
from apiclient import discovery
import sys
from flask import jsonify, redirect
from flask import render_template
from flask import Flask
from os import environ
from oauth2client.service_account import ServiceAccountCredentials
import time
from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPProxyAuth
from fake_useragent import UserAgent

app = Flask(__name__, template_folder='template')


@app.route("/")
def hello():
    return render_template('/index.html')


@app.route("/success")
def success():
    return render_template('/index.html')


@app.route("/ping")
def ping():
    return jsonify(success=True)


@app.route("/process")
def process():
    t = Test()
    t.search_google()
    return redirect(url_for('success'))


class Test:
    def __init__(self):
        self.ua = UserAgent()
        self.scope = ['https://www.googleapis.com/auth/drive',
                      'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']

    def search_google(self):
        SAMPLE_SPREADSHEET_ID = '1emESVdaG4MCiTi9v1q6-B6rKlFbaLuvCLwHZQvo2W0o'
        SAMPLE_RANGE_NAME = 'A2:A'

        secret_file = os.path.join(os.getcwd(), 'credentials.json')

        credentials = service_account.Credentials.from_service_account_file(
            secret_file, scopes=self.scope)
        self.sheets = discovery.build(
            'sheets', 'v4', credentials=credentials)

        sheet = self.sheets.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        write_arr = []
        if values:
            print(
                '-----------------------------------BATCH STARTS-----------------------------------')
            for x in values:
                for y in x:
                    req_url = str(y).strip()
                    print(req_url)
                    payload = {
                        'api_key': '4597a316740a95bfcb52eade5ac54a9b', 'url': req_url, 'keep_headers': 'true'}
                    header = {'User-Agent': str(self.ua.ff)}
                    success = False
                    count = 0
                    while success == False:
                        try:
                            result_page = requests.get(
                                'http://api.scraperapi.com', params=payload, headers=header)
                            soup = BeautifulSoup(result_page.text, 'lxml')
                            results_tag = soup.find(
                                'div', attrs={"id": "search"})

                            if results_tag:
                                row_arr = []

                                web_results = results_tag.find(
                                    lambda tag: tag.name == 'h2' and tag.text == 'Web results'
                                )
                                if web_results:
                                    sibling = web_results.next_sibling
                                    if sibling:
                                        g_tags = sibling.find_all(
                                            'div', attrs={"class": "g"})
                                        if g_tags:
                                            g_tag = g_tags[0]
                                            r_tag = g_tag.find(
                                                'div', attrs={"class": "r"}, recursive=True)
                                            if r_tag is None:
                                                r_tag = g_tag.find(
                                                    'h3', attrs={"class": "r"}, recursive=True)
                                            s_tag = g_tag.find(
                                                'div', attrs={"class": "s"}, recursive=True)

                                            title = r_tag.find(
                                                'h3', recursive=True).text
                                            cite = s_tag.find('cite', recursive=True)
                                            if cite:
                                                url = str(cite.text)
                                            else:
                                                url = str(r_tag.find(
                                                    'a', recursive=True)['href'])
                                            description = s_tag.find(
                                                'span', attrs={"class": "st"}, recursive=True).text

                                            row_arr.append(title)
                                            row_arr.append(url)
                                            row_arr.append(description)
                                            write_arr.append(row_arr)

                                            print('Title: ' + title)
                                            print('URL: ' + url)
                                            print('Description: ' + description)
                                            success = True
                                        else:
                                            print('G tag not found')
                                            count = count + 1
                                            if count > 5:
                                                success = True
                                                row_arr.append('NO RESULTS')
                                                row_arr.append('')
                                                row_arr.append('')
                                                write_arr.append(row_arr)
                                    else:
                                        print('sibling tag not found')
                                        count = count + 1
                                        if count > 5:
                                            success = True
                                            row_arr.append('NO RESULTS')
                                            row_arr.append('')
                                            row_arr.append('')
                                            write_arr.append(row_arr)
                                else:
                                    print('web results tag not found')
                                    count = count + 1
                                    if count > 5:
                                        success = True
                                        row_arr.append('NO RESULTS')
                                        row_arr.append('')
                                        row_arr.append('')
                                        write_arr.append(row_arr)
                            else:
                                print('result tag not found')
                                count = count + 1
                                if count > 5:
                                    success = True
                                    row_arr.append('NO RESULTS')
                                    row_arr.append('')
                                    row_arr.append('')
                                    write_arr.append(row_arr)
                        except:
                            print("Unexpected error:", sys.exc_info())
                            pass
            print(
                '-----------------------------------BATCH ENDS-----------------------------------')
            Body = {
                'values': write_arr,
            }
            range = 'B2:D'+str(len(write_arr) + 1)
            request = self.sheets.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                                 range=range, valueInputOption='RAW', insertDataOption='OVERWRITE', body=Body)
            response = request.execute()
            print(response)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=False)
