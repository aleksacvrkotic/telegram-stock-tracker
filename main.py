from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tabulate import tabulate
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import time

TOKEN = 'YOUR_TOKEN'

url = 'https://www.marketwatch.com/investing/stock/djia'
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_service = Service()
tracking_enabled = True

#Calculating the changes from previous close
def up_down_calc(driver, current_value):
    prev_close = driver.find_element(By.CSS_SELECTOR, 'td.table__cell.u-semi').text.replace(",", "").replace("$", "")
    prev_close = round(float(prev_close), 2)
    flat_value = round((current_value - prev_close), 2)
    proc_value = round((flat_value/prev_close)*100, 2)
    return flat_value, proc_value

#Extracting the keyData
def getting_key_data(driver):
    df = {}
    #Waiting for element to be present
    WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'li.kv__item')))
    key_data_containers = driver.find_elements(By.CSS_SELECTOR, 'li.kv__item')
    for key_data_container in key_data_containers:
        label = key_data_container.find_element(By.CSS_SELECTOR, 'small.label').text
        value = key_data_container.find_element(By.CSS_SELECTOR, 'span.primary').text
        df[f'{label}'] = value
    return df

# initialize the driver and get the bassic info every time it is called
def initialize_driver():
    global close_button, comp_name, old_price, status

    close_button = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(('css selector', "button.close-btn"))).click()

    comp_name = driver.find_element('css selector', 'h1.company__name').text
    old_price = driver.find_element('css selector', 'h2.intraday__price').text.replace(",", "").replace("$\n", "").strip()
    old_price = round(float(old_price), 2)
    status = driver.find_element(By.CSS_SELECTOR, 'div.status').text
    print(status)





# The first message you will se
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('   Hi, I am a stock tracker bot. If you wish to track the price of your favorite stock plese use  /setstockindex command first. If you need further help just use /help for additional information.')

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""I can help you track your favorite stock price live!!

The default stock that is set to the bot is Dow Jones Industrial Average.
So the first thing you should do is set your target stock index and then use any command that you would like.

Commands:

/setstockindex [Your stock index] - set the stock index that you would like to track

/status - check the status of the stock market

/track - start tracking the price

/stop - stop tracking the price

/keydata - get the Key Data
""")
# Get the status of the stock market
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(status)

# Get the key data and send it to the user
async def key_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global driver
    await update.message.reply_text("Getting the Key Data...")
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)  # Create a new driver instance
    await load_url(driver)  # Reload the URL to get updated data

    # Initialize the driver and variables
    initialize_driver()

    key_data = getting_key_data(driver)
    table_data = [(key, value) for key, value in key_data.items()]
    table_string = tabulate(table_data, tablefmt="grid")
    await update.message.reply_text(table_string)

#The command for changing the target stock index
async def set_stock_index_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global url, driver
    if len(context.args) > 0:
        stock_index = context.args[0]
        await update.message.reply_text(f'Seetting Stock Index to: {stock_index}...')
        new_url = f'https://www.marketwatch.com/investing/stock/{stock_index}'

        # Close the existing driver
        driver.quit()
        # Create a new driver instance
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        # Update the URL
        url = new_url
        # Load the new URL
        await load_url(driver)
        # Initialize the driver and variables
        initialize_driver()
        await update.message.reply_text(f'Stock index set to: {stock_index}')
    else:
        await update.message.reply_text('Please provide a stock index.')

# The loop that tracks the price when tracking_enabled is True
async def track_stock_loop(bot: Bot):
    global tracking_enabled, driver, old_price

    if tracking_enabled:
        while True:
            print('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')
            if not tracking_enabled:
                print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
                break

            # Simulate a random price update
            new_price = round(old_price + random.uniform(-1, 1), 2)

            change = round((old_price - new_price), 2)
            from_previous_close_flat, from_previous_close_percentage = up_down_calc(driver, new_price)

            update_string = f"Company Name: {comp_name}\nCurrent Price: {new_price}$\nChange: {change}$\nFlat Change From Previous Close: {from_previous_close_flat}$\n% Change From Previous Close: {from_previous_close_percentage}%\n"
            old_price = new_price

            print(update_string)
            await bot.send_message(chat_id=5091782216, text=update_string)

            await asyncio.sleep(5)  # Delay between each iteration

#/track to start the tracking
async def start_tracking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tracking_enabled

    if not tracking_enabled:
        tracking_enabled = True
        await update.message.reply_text('Tracking started.')
        loop.create_task(track_stock_loop(app.bot))
        print(tracking_enabled)

#/stop to stop the tracking
async def stop_tracking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global tracking_enabled

    if tracking_enabled:
        tracking_enabled = False
        await update.message.reply_text('Tracking stopped.')
    else:
        await update.message.reply_text('Tracking is not currently enabled.')

#Error logging
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

#url update
async def load_url(driver):
    driver.get(url)

if __name__ == '__main__':
    # Create the driver instance
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # Load the initial URL
    loop = asyncio.get_event_loop()
    loop.run_until_complete(load_url(driver))

    # Telegram bot setup
    app = Application.builder().token(TOKEN).build()
    #Declaring the commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('keydata', key_data_command))
    app.add_handler(CommandHandler('setstockindex', set_stock_index_command))
    app.add_handler(CommandHandler('track', start_tracking_command))
    app.add_handler(CommandHandler('stop', stop_tracking_command))
    #handling the error
    app.add_error_handler(error)

    # Start tracking stock in a separate task
    loop.create_task(track_stock_loop(app.bot))

    print('Polling...')
    app.run_polling(poll_interval=5)
