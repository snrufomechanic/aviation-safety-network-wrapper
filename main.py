import requests
from bs4 import BeautifulSoup

homepage = 'https://aviation-safety.net/wikibase/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 '
                  'Safari/537.36',
}


def get_years():
    html = requests.get(homepage, headers=headers).text

    soup = BeautifulSoup(html, 'html.parser')

    # Update the selector for year links
    year_links = soup.select('#contentcolumn a[href^="/wikibase/dblist.php?Year="]')

    # Extract the href attribute from each link
    years = [link['href'].split('=')[-1] for link in year_links]

    return years


def get_page_info(year):
    url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}'
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, 'html.parser')

    pages = soup.find('div', class_='pagenumbers')
    if pages: #!TODO: Saçma site tek sayfa veri olsa bile pagenumbers class'ı var. Buranın düzeltilmesi lazım.
        page_links = pages.find_all('a')

        page_count = len(page_links)
        print(page_count)
        return page_count
    else:
        return 1


def get_accidents(year, page_number):
    #!NOTE: Dünya Savaşlarının olduğu yıllar uzun sürüyor. her page için async func çağırılabilir.
    if page_number == 1:
        url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}'
    else:
        url = f'http://aviation-safety.net/wikibase/dblist.php?Year={year}&sorteer=datekey&page={page_number}'

    html = requests.get(url, headers=headers).text

    soup = BeautifulSoup(html, 'html.parser')

    # Print the HTML content for debugging

    # Select table class="hp"
    table = soup.find('table', class_='hp')

    # Check if the table is found
    if table:

        # Select all rows except the first one
        rows = table.find_all('tr')

        accidents_data = []

        for row in rows[1:]:
            # Extract information from each column in the row
            columns = row.select('td')

            # Check if there are columns (avoid header row)
            if columns:
                date = columns[0].text.strip()
                aircraft_type = columns[1].text.strip()
                registration = columns[2].text.strip()
                operator = columns[3].text.strip()
                fatalities = columns[4].text.strip()
                location = columns[5].text.strip()
                flag = columns[6].text.strip(),
                dmg = columns[7].text.strip(),

                # Create a dictionary to store the information
                accident_info = {
                    'date': date,
                    'aircraft_type': aircraft_type,
                    'registration': registration,
                    'operator': operator,
                    'fatalities': fatalities,
                    'location': location,
                    'flag': flag,
                    'dmg': dmg #!TODO: çekilen stringlerde ('....') yapısı olduğu zaman exel'de kaymalara neden oluyor.
                }

                print(accident_info)

                accidents_data.append(accident_info)

        return accidents_data
    else:
        print("Table not found on the page.")
        return []


def main():
    years = get_years()
    all_accidents = []
    for year in years:
        page_number = get_page_info(year)
        for page in range(1, page_number + 1):
            accidents = get_accidents(year, page)
            all_accidents.extend(accidents)

    # Save the data to a CSV file
    with open('accidents.csv', 'w', encoding='utf-8') as f:
        f.write('Date,Aircraft type,Registration,Operator,Fatalities,Location,Flag,Dmg\n')
        for accident in all_accidents:
            f.write(f"{accident['date']},{accident['aircraft_type']},{accident['registration']},{accident['operator']},"
                    f"{accident['fatalities']},{accident['location']},{accident['flag']},{accident['dmg']}\n")


if __name__ == '__main__':
    main()
