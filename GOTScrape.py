import pandas as pd
from bs4 import BeautifulSoup
import requests


def containerExtract(container):
    epString = container.a.div.div.text.split(', ')

    title = container.find('strong').text
    airDate = container.find('div', class_='airdate').text
    rating = container.find('span', class_='ipl-rating-star__rating').text
    votes = container.find('span', class_='ipl-rating-star__total-votes').text
    votes = votes.replace('(', '').replace(')', '').replace(',', '')
    link = container.strong.a['href']

    dataDict = dict(season=int(epString[0].replace('S', '')),
                    episode=int(epString[1].replace('Ep', '')),
                    title=title,
                    airDate=airDate.strip(),
                    rating=float(rating),
                    votes=int(votes),
                    link=link)

    return dataDict


def seasonDF(season):
    # Fetch page 
    urlString = 'https://www.imdb.com/title/tt0944947/episodes?season={}'.format(season)
    response = requests.get(urlString)
    soup = BeautifulSoup(response.text, 'lxml')

    # Collect summary containers
    ep_containers = soup.find_all('div', class_=['list_item odd', 'list_item even'])
    dictList = []
    for ep in ep_containers:
        dictList.append(containerExtract(ep))
    df = pd.DataFrame(dictList)
    return df


def creditDF(link, season, episode):
    url = 'http://www.imdb.com' + link + 'fullcredits?ref_=tt_ov_wr/'
    response = requests.get(url)
    epSoup = BeautifulSoup(response.text, 'lxml')

    # 
    fieldList = epSoup.find_all('h4', class_='dataHeaderWithBorder', id=False)
    tableList = epSoup.find_all('table', class_=['simpleTable simpleCreditsTable'])
    castList = [c.text.strip() for c in epSoup.find('table', class_=['cast_list']).find_all('td', class_=False)]
    credList = []

    for f, t in zip(fieldList, tableList):
        tableName = f.text.strip()
        names = [s.text.strip() for s in t.find_all('a')]
        credDict = dict(creditType=tableName, name=names)
        credList.append(pd.DataFrame(credDict))
    credList.append(pd.DataFrame(
        dict(creditType='Cast',
             name=castList))
    )
    df = pd.concat(credList).reset_index(drop=True)
    df['season'] = season
    df['episode'] = episode
    df.drop_duplicates(inplace=True)

    return df


# Collect and Clean episode summary
episodes = []
for s in range(1, 9):
    df = seasonDF(s)
    episodes.append(df)
episodes = pd.concat(episodes)

episodes = episodes[['season', 'episode', 'airDate', 'title', 'rating', 'votes', 'link']].reset_index(drop=True)
episodes.to_csv('episodes.csv', index=False)
print('CSV created')

# collect Cast & crew data
credits = []
for l, s, e in episodes[['link', 'season', 'episode']].values:
    df = creditDF(link=l, season=s, episode=e)
    credits.append(df)
    print('S{}E{} complete'.format(s, e))
credits = pd.concat(credits, sort=False)
credits.to_csv('credits.csv', index=False)
print('CSV created')
