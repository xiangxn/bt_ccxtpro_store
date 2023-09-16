import sys

sys.path.append(".")
import time
from datetime import datetime, timedelta
import backtrader as bt
from ccxtpro import CCXTProStore
import asyncio


def main():

    class TestStrategy(bt.Strategy):

        params = (("period_boll", 275), ("price_diff", 20), ('small_cotter', 10), ("production", False), ("debug", True), ('reversal', False))

        def __init__(self):
            self.next_runs = 0
            self.boll = bt.indicators.bollinger.BollingerBands(self.datas[0], period=self.p.period_boll)

        def debug(self, txt, dt=None):
            dt = dt or self.datas[0].datetime.datetime(0)
            # self.logger.debug(f'[{dt}]: {txt}')
            print(f'[{dt}]: {txt}')

        def next(self, dt=None):
            print("d2:", self.datas[1].volume[0])
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
            # print("prenext.....")
            # print("len:", len(self.datas))
            # print("prenext d1:", self.data0.volume[0], self.data0.close[0])
            # print("prenext d2:", self.data1.volume[0], self.data1.close[0])
            # if self.p.production and not self.live_data:
            #     for data in self.datas:
            #         self.debug(' {} | O: {} H: {} L: {} C: {} V:{}'.format(data._name, data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0]))
            # else:
            #     for data in self.datas:
            #         self.debug(' {} | O: {} H: {} L: {} C: {} V:{}'.format(data._name, data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0]))
            pass

    cerebro = bt.Cerebro()



    config = { 'enableRateLimit': True, 'requests_trust_env': True, 'aiohttp_trust_env': True, 'OHLCVLimit': 1500, 'options': { 'defaultType': 'future'} }
    config2 = { 'enableRateLimit': True, 'requests_trust_env': True, 'aiohttp_trust_env': True, 'OHLCVLimit': 1500, 'options': { 'defaultType': 'spot'} }
    store = CCXTProStore(exchange='binanceusdm', currency='USDT', config=config, retries=10, debug=True)

    hist_start_date = datetime.utcnow() - timedelta(minutes=1370)
    data = store.getdata(
        dataname='ETH/USDT',
        name="future",
        timeframe=bt.TimeFrame.Minutes,
        fromdate=hist_start_date,
        compression=5,
        ohlcv_limit=99999,
        drop_newest=True,
        # historical=True
    )

    # Add the feed
    cerebro.adddata(data, name="future")

    s2 = CCXTProStore(exchange='binance', currency='USDT', config=config2, retries=10, debug=True)
    d2 = s2.getdata(
        dataname='ETH/USDT',
        name="spot",
        timeframe=bt.TimeFrame.Minutes,
        fromdate=hist_start_date,
        compression=5,
        ohlcv_limit=99999,
        drop_newest=True,
        # historical=True
    )
    cerebro.adddata(d2, name="spot")

    cerebro.addstrategy(TestStrategy)

    # Run the strategy
    task = asyncio.ensure_future(cerebro.run())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([task]))


if __name__ == '__main__':
    main()
