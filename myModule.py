from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re
import api_keys

client = OpenAI(
    api_key=api_keys.open_AI_API_key,
)
model = api_keys.open_AI_GPT_model

def retrieve_html(url, flag):

    if flag == 'blog':

        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            raise Exception(response.reason)

    else:

        try:
            response = requests.get(url, timeout=5)
        except:
            print('Error: cannot fetch the Webpage')
            return ''
        
        if response.status_code != 200:
            print('Error: cannot fetch the Webpage')
            return ''
    
    html = response.text

    soup = BeautifulSoup(html, 'html.parser')

    title_tag = soup.find('meta', property='og:title') or soup.find('meta', property='twitter:title') or soup.find('title')
    title = title_tag.get('content') if title_tag else ''
    description_tag = soup.find('meta', property='og:description') or soup.find('meta', property='twitter:description') or soup.find('meta', attrs={'name': 'description'})
    description = description_tag.get('content') if description_tag else ''

    text = soup.get_text()

    if title and description:
        text = "Meta Title: " + title + "\nMeta Desciption: " + description + '\nContent:' + text
    else:
        if title:
            text = "Meta Title: " + title + '\nContent:' + text
        elif description:
            text = "Meta Desciption: " + description + '\nContent:' + text

    content = re.sub(r'[^\w\s.,!?:\'"]', '', text)

    return content

def extract_keywords_using_ChatGPT(content):

    keyword_dict = {}

    try:

        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system",
                "content": "You are a SEO tool that can help me to remove stop words and extract 20 important keywords, bigram and trigram phrases from the given text based on the frequency of their usage and importance of them in the context of blog and output them as a numbered list."},
                {"role": "user",
                "content": content}
            ]
        )
        response = chat_completion.choices[0].message.content

    except:

        raise Exception('ChatGPT is incapable of processing the request')

    print('reponse for keywords:\n', response)

    keywords = response.split('\n')
    content = content.lower()

    for keyword in keywords:
        if re.match(r'^\d+\.', keyword):
            keyword = re.sub(r'^\d+\.', '', keyword)
            keyword = re.sub(r'\([^)]*\)', '', keyword).strip().strip('"').strip()
        elif keyword.startswith('-'):
            keyword = re.sub(r'\([^)]*\)', '', keyword.strip('-')).strip().strip('"').strip()
        else:
            keyword = ''
        keyword = keyword.lower()
        if keyword and keyword not in keyword_dict:
            keyword_count = content.count(keyword)
            keyword_dict[keyword] = keyword_count if keyword_count > 0 else 1

    print("keywords:\n", keyword_dict)

    return keyword_dict

def count_frequencies_in_blog(blog, keywords):
    
    keyword_dict = {}
    blog = blog.lower()
    keywords = [keyword.strip().lower() for keyword in keywords.strip(',').split(',')]

    for keyword in keywords:

        keyword_dict[keyword] = blog.count(keyword)

    return keyword_dict


def extract_keywords(content, input_type, keywords=''):

    print("Inside extract_keywords function:")
    print("input_type:", input_type)
    print("content:", content)
    keyword_dict = {}

    if input_type == 'URL_with_Keywords':

        content = retrieve_html(content, 'blog')
        if not content:
            return {}
        
        keyword_dict = count_frequencies_in_blog(content, keywords)

    elif input_type == 'URL_without_Keywords':

        content = retrieve_html(content, 'blog')
        if not content:
            return {}
        
        keyword_dict = extract_keywords_using_ChatGPT(content)

    elif input_type == 'Blog_with_Keywords':

        keyword_dict = count_frequencies_in_blog(content, keywords)

    elif input_type == 'Blog_without_Keywords':

        keyword_dict = extract_keywords_using_ChatGPT(content)
        
    return keyword_dict


def determine_color(keyword):
    
    if keyword['blog_count'] < keyword['min'] or keyword['blog_count'] > keyword['max']:

        return 'red'
    
    else:

        range = abs(keyword['blog_count']-keyword['avg'])/keyword['avg']

        if range > 0.25:

            return 'yellow'
        
        else:

            return 'green'
        

def process_input(blog_keywords):

    blog_keywords_with_color = {}

    for blog_keyword in blog_keywords:

        temp_dict = {}

        payload = {
            'key': api_keys.google_api_key,
            'cx': api_keys.cx_key,
            # 'exactTerms': blog_keyword,
            'q': blog_keyword,
            # 'lr': 'lang_en',
            'num': 10
        }
        
        response = requests.get('https://www.googleapis.com/customsearch/v1', params=payload)

        frequencies = []

        for webpage in response.json()['items']:

            URL = webpage['formattedUrl']

            print('Webpage URL:', URL)

            webcontent = retrieve_html(URL, 'webpage')
            print(webcontent)
            webcontent = webcontent.lower()

            if webcontent:
                keyword_count = webcontent.count(blog_keyword)

                if keyword_count:

                    print(keyword_count)

                    frequencies.append(keyword_count)

        print('frequencies: ', frequencies)
        if frequencies:
            blog_keywords_with_color[blog_keyword] = {'blog_count': blog_keywords[blog_keyword],
                                                    'min': min(frequencies),
                                                    'max': max(frequencies),
                                                    'webpage_count': len(frequencies),
                                                    'avg': int(sum(frequencies)/len(frequencies))}
            color = determine_color(blog_keywords_with_color[blog_keyword])
            blog_keywords_with_color[blog_keyword]['color'] = color
        
    print(blog_keywords_with_color)
    return blog_keywords_with_color

def beautify(keywords):

    html_content = '<li class="keywordItem grey"> Keyword <span class="stats"> Keyword Count in Blog / Minimum Count in Webpages - Maximum Count in Webpages / Average Count in Webpages </span></li><br>'
    color_order = {'red': 1, 'yellow': 2, 'green': 3}
    sorted_data = sorted(keywords.items(), key=lambda x: color_order[x[1]['color']])

    for keyword, stats in sorted_data:
        html_content += '<li class="keywordItem ' + stats['color'] + '">' + keyword + '<span class="stats">' + str(stats['blog_count']) + ' / ' + str(stats['min']) + ' - ' + str(stats['max']) + ' / ' + str(stats['avg']) + '</span></li>'

    print(html_content)
    return html_content