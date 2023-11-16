import logging
import pandas as pd
import aiohttp
import asyncio
import sqlite3
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

user_agent = UserAgent()
homepage = 'https://aviation-safety.net/wikibase/'

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def create_db():
    conn = sqlite3.connect('accidents.db')
    cursor = conn.cursor()

    # Check if the 'accidents' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accidents';")
    table_exists = cursor.fetchone()

    if not table_exists:
        # If the table doesn't exist, create it
        cursor.execute('''
            CREATE TABLE accidents (
                Date TEXT,
                [Aircraft Type] TEXT,
                Registration TEXT,
                Operator TEXT,
                Fatalities TEXT,
                Location TEXT,
                Flag TEXT,
                Dmg TEXT
            );
        ''')
        logging.info("Table 'accidents' created.")

    conn.close()


async def get_existing_start_year():
    await create_db()  # Ensure the 'accidents' table exists

    conn = sqlite3.connect('accidents.db')
    cursor = conn.cursor()

    cursor.execute("SELECT Date FROM accidents ORDER BY Date DESC LIMIT 1")
    last_date_text = cursor.fetchone()

    conn.close()

    if last_date_text:
        last_date_text = last_date_text[0]
        logging.info(f"Last date in the database: {last_date_text}")

        if isinstance(last_date_text, str):
            last_date = pd.to_datetime(last_date_text).date()
            last_year = last_date.year
            logging.info(f"Last year: {last_year}")
            return last_year, last_date
        else:
            return None, None

    return None, None


async def save_to_database(accidents_for_year):
    conn = sqlite3.connect('accidents.db')
    accidents_for_year.to_sql('accidents', conn, if_exists='append', index=False)
    conn.close()


async def get_years():
    async with aiohttp.ClientSession() as session:
        async with session.get(homepage, headers={'User-Agent': user_agent.random}) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')
    year_links = soup.select('#contentcolumn a[href^="/wikibase/dblist.php?Year="]')
    years = [link['href'].split('=')[-1] for link in year_links]

    return years


async def get_page_info(year):
    url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': user_agent.random}) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')

    pages = soup.find('div', class_='pagenumbers')
    if pages:
        page_links = pages.find_all('a')

        page_count = len(page_links)
        logging.info(f"{page_count} pages of data were found for {year}. The assembly process begins.")
        return page_count
    else:
        return 1


async def get_accidents(year, page_number):
    logging.info(f"Data on accidents that occurred in {year} began to be collected. The {page_number}nd page is currently being collected.")
    if page_number == 1:
        url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}'
    else:
        url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}&sorteer=datekey&page={page_number}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={'User-Agent': user_agent.random}) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='hp')

    if table:
        rows = table.find_all('tr')
        accidents_data = []

        for row in rows[1:]:
            columns = row.select('td')

            if columns:
                date = columns[0].text.strip()
                aircraft_type = columns[1].text.strip()
                registration = columns[2].text.strip()
                operator = columns[3].text.strip()
                fatalities = columns[4].text.strip()
                location = columns[5].text.strip()
                flag = columns[6].text.strip()
                dmg = columns[7].text.strip()

                accident_info = {
                    'Date': date,
                    'Aircraft Type': aircraft_type,
                    'Registration': registration,
                    'Operator': operator,
                    'Fatalities': fatalities,
                    'Location': location,
                    'Flag': flag,
                    'Dmg': dmg
                }

                accidents_data.append(accident_info)

        accidents_for_year = pd.DataFrame(accidents_data)

        # Düzeltme: Geçersiz tarihleri filtrele
        accidents_for_year = accidents_for_year[accidents_for_year['Date'].str.match(r'\d{2}-[a-zA-Z]{3}-\d{4}')]

        # Düzeltme: Tarih formatını belirt
        accidents_for_year['Date'] = pd.to_datetime(accidents_for_year['Date'], format='%d-%b-%Y', errors='coerce').dt.date

        await save_to_database(accidents_for_year)
    else:
        logging.warning("Table not found on the page.")
        logging.debug(f"HTML content:\n{html}")

async def main():
    last_year, last_date = await get_existing_start_year()

    if last_year is not None:
        years = list(range(last_year, 2023))
    else:
        years = await get_years()

    for year in years:
        page_number = await get_page_info(year)

        tasks = [get_accidents(year, page) for page in range(1, page_number + 1)]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())