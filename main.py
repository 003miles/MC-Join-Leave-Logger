from config import config
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os


def timeMe(method):
    def wrapper(*args, **kw):
        startTime = int(round(time.time() * 1000))
        result = method(*args, **kw)
        endTime = int(round(time.time() * 1000))
        print("Execution time: {}s".format((endTime - startTime) / 1000))
        return result

    return wrapper


@timeMe
def main():
    #   Config
    options = Options()
    options.headless = config['headless']
    # driver = webdriver.Chrome('./chromedriver', options=options)
    driver = webdriver.Chrome(ChromeDriverManager().install(),
                              options=options)

    email = config['email']
    password = config['password']

    IGNs = config['IGNs']

    suffix = config['searchSuffix']

    scrapes = []

    driver.get(config['channel'])

    #   Login
    driver.find_element_by_xpath(
        '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[1]/div/div[2]/input').send_keys(
        email)
    driver.find_element_by_xpath(
        '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[2]/div/input').send_keys(
        password)
    driver.find_element_by_xpath(
        '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/button[2]').click()
    print('Logged in.')

    #   Search for player join/leave logs
    for ign in IGNs:
        scrape = []

        while True:
            try:
                driver.find_element_by_xpath(
                    '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[2]/section/div[2]/div[4]/div/div/div[1]/div[2]/div/div/div').send_keys(
                    f'{ign} {suffix}', Keys.ENTER)
                break
            except:
                continue

        time.sleep(1)
        driver.find_element_by_xpath(
            '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/section/div[1]/div[3]').click()
        print('Found logs.')

        #   Scrape data from message

        while True:
            try:
                noResults = int(driver.find_element_by_xpath(
                    '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/section/div[1]/div[1]/div').text.split()[
                                    0].replace(',', ''))
                break
            except:
                continue

        print(f'Getting logs for {ign}...')
        index = 0
        # noinspection PyUnboundLocalVariable
        for i in range(noResults + 1):
            try:
                msgID = driver.find_element_by_xpath(f'//*[@id="search-results-{index}"]/div/div').get_attribute(
                    'data-list-item-id').split('_')[-1]
            except:
                index = 0
                try:
                    driver.find_element_by_xpath(
                        '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[2]/div[2]/section/div[2]/div[2]/div/nav/button[2]').click()
                    time.sleep(2)
                    continue
                except:
                    break

            msg = driver.find_element_by_xpath(f'//*[@id="search-results-{index}"]/div/div/div[2]').get_attribute(
                'innerText')

            if 'joined' in msg:
                jL = 'Joined'
            elif 'left' in msg:
                jL = 'Left'
            else:
                index += 1
                continue

            scrape.append(
                {
                    'id': msgID,
                    'joined/left': jL,
                    'date': None,
                    'time': None
                }
            )

            index += 1

        scrapes.append(
            {
                'ign': ign,
                'j/l times': scrape
            }
        )
        print('Done.')
        driver.refresh()

    #   Get date and time from message IDs
    print('Getting dates and times...')
    for scrape in scrapes:
        for i in scrape['j/l times']:
            driver.get(f"https://pixelatomy.com/snow-stamp/?s={i['id']}")
            datetime = driver.find_element_by_xpath('/html/body/main/section/p[2]/time').text.split(', ')

            i['date'] = datetime[0]
            i['time'] = datetime[1]

    driver.close()
    print('Finished.')

    #   Final output
    for i in scrapes:
        print(f"IGN: {i['ign']}\n    Join/Leave Log:")
        for j in i['j/l times']:
            j.pop('id')  # Excludes message ID from final output
            print(f"        {j['joined/left']} - {j['date']}, {j['time']}")

        #   Save join/leave log to csv sheet
        df = pd.json_normalize(i['j/l times'])

        fileName = f"LOGS/{i['ign']} LOG.csv"
        os.makedirs(os.path.dirname(fileName), exist_ok=True)
        df.to_csv(fileName, index=False, encoding='utf-8')

    print('See LOGS folder for csv sheets.')


if __name__ == '__main__':
    main()
