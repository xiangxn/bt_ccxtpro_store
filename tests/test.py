import sys

sys.path.append(".")
import time
from datetime import datetime, timedelta
import backtrader as bt
from ccxtpro import CCXTProStore
import asyncio


def main():

    class TestStrategy(bt.Strategy):

        params = (("production", True), )

        def __init__(self):
            self.next_runs = 0

        def debug(self, txt, dt=None):
            dt = dt or self.datas[0].datetime.datetime(0)
            # self.logger.debug(f'[{dt}]: {txt}')
            print(f'[{dt}]: {txt}')

        def next(self, dt=None):
            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s closing price: %s' % (dt.isoformat(), self.datas[0].close[0]))
            self.next_runs += 1

        def notify_data(self, data, status, *args, **kwargs):
            dn = data._name
            dt = datetime.utcnow()
            msg = 'Data Status: {}'.format(data._getstatusname(status))
            print(dt, dn, msg)
            if data._getstatusname(status) == 'LIVE':
                self.live_data = True
            else:
                self.live_data = False

        def prenext(self):
            print("prenext.....")
            if self.p.production and not self.live_data:
                for data in self.datas:
                    self.debug(' {} | O: {} H: {} L: {} C: {} V:{}'.format(data._name, data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0]))
            else:
                data = self.datas[0]
                self.debug(' {} | O: {} H: {} L: {} C: {} V:{}'.format(data._name, data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0]))

    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    config = { 'enableRateLimit': True, 'requests_trust_env': True, 'aiohttp_trust_env': True, 'OHLCVLimit': 1500 }
    store = CCXTProStore(exchange='binanceusdm', currency='USDT', config=config, retries=10, debug=True)
    hist_start_date = datetime.utcnow() - timedelta(minutes=1370)
    data = store.getdata(
        dataname='ETH/USDT',
        name="ETHUSDT",
        timeframe=bt.TimeFrame.Minutes,
        fromdate=hist_start_date,
        compression=5,
        ohlcv_limit=99999,
        # drop_newest=True,
        # historical=True
    )

    # Add the feed
    cerebro.adddata(data)

    # Run the strategy
    task = asyncio.ensure_future(cerebro.run())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([task]))


if __name__ == '__main__':
    main()
