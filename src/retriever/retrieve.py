"""
    retrieve.py
    (c) J. Renero

    This module retrieves latest OHLCV info and updates corresponding file.

"""
import sys
from datetime import datetime
from retriever.closing import Closing
from retriever.rt_dictionary import RTDictionary
from utils.last import last


def main(argv):
    """
    Retrieve the latest stock info about the symbol and check if dates match
    """
    params = RTDictionary(args=argv)
    log = params.log

    # Call the proper service to retrieve stock info.
    stock_data, stock_date = Closing.retrieve_stock_data(params)

    if params.file is None:
        print(stock_data)
        return

    today = datetime.today().strftime('%Y-%m-%d')
    last_date_in_file = last.row_date(params.file)
    log.info('Retrieved data for {} by <{}>'.format(params.symbol, stock_date))
    log.info('Last date in file <{}>'.format(last_date_in_file))

    # If stock data date does not match last working day, we've a problem...
    last_working_day = last.working_day(country=params.country)
    if stock_date != last_working_day and stock_date != today:
        msg = 'Latest stock DATE does not match last working day\n'
        msg += '  {} != {}'.format(stock_date, last_working_day)
        raise ValueError(msg)

    # If data coming in is from today, stop.
    elif stock_date == today and last_date_in_file != last_working_day:
        msg = 'Stock data from API is TODAY\'s data. Stopping.\n'
        msg += 'Latest row in OHLC file is not last working day\'s {}.'.format(
            last_working_day)
        raise ValueError(msg)
    elif stock_date == today and last_date_in_file == last_working_day:
        log.warn('Data already in file for date <{}>. Doing nothing'.format(
            last_date_in_file))
        return

    # Determine the name of the temporary JSON file, from the stock symbol
    json_file = params.json_file.format(params.symbol)

    # Build the CSV row to be added to the OHLC file, with latest info.
    row = Closing.csv_row(stock_data, params.json_columns,
                          params.ohlc_columns, json_file, params.log)
    # Append that CSV row.
    Closing.append_to_file(row, params.file, last_working_day, params.log)


if __name__ == "__main__":
    main(sys.argv)
