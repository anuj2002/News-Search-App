from flask import Flask, render_template, request
import pandas as pd
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

def clean_url(searched_item, data_filter):
    """
    Generate the URL to fetch news based on the search term and date filter.
    """
    x = pd.datetime.today()
    today = str(x)[:10]
    yesterday = str(x + pd.Timedelta(days=-1))[:10]
    this_week = str(x + pd.Timedelta(days=-7))[:10]
    
    if data_filter == 'today':
        time_filter = 'after%3A' + yesterday
    elif data_filter == 'this_week':
        time_filter = 'after%3A' + this_week + '+before%3A' + today
    elif data_filter == 'this_year':
        time_filter = 'after%3A' + str(x.year - 1)
    elif str(data_filter).isdigit():
        temp_time = str(x + pd.Timedelta(days=-int(data_filter)))[:10]
        time_filter = 'after%3A' + temp_time + '+before%3A' + today
    else:
        time_filter = ''
    
    url = f'https://news.google.com/rss/search?q={searched_item}+' + time_filter + '&hl=en-US&gl=US&ceid=US%3Aen'
    return url

def get_text(x):
    """
    Extract text from the description.
    """
    start = x.find('<p>') + 3
    end = x.find('</p>')
    return x[start:end]

def get_news(search_term, data_filter=None):
    """
    Fetch news headlines and details from Google News based on search term and date filter.
    """
    url = clean_url(search_term, data_filter)
    response = requests.get(url)
    root = ET.fromstring(response.text)
    
    title = [i.text for i in root.findall('.//channel/item/title')]
    link = [i.text for i in root.findall('.//channel/item/link')]
    description = [i.text for i in root.findall('.//channel/item/description')]
    pubDate = [i.text for i in root.findall('.//channel/item/pubDate')]
    source = [i.text for i in root.findall('.//channel/item/source')]
    
    short_description = list(map(get_text, description))
    
    df = pd.DataFrame({'title': title, 'link': link, 'description': short_description, 'date': pubDate, 'source': source})
    df.date = pd.to_datetime(df.date, unit='ns')
    df.to_csv(f'{search_term}_news.csv', encoding='utf-8-sig', index=False)
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form['search_term']
        data_filter = request.form['data_filter']
        data = get_news(search_term, data_filter)
        data_list = data.to_dict(orient='records')
        return render_template('index.html', data=data_list)

    return render_template('index.html', data=None)

if __name__ == "__main__":
    app.run(debug=True)
