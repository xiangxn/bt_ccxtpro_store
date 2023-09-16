#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2017 Ed Bartosh <bartosh@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import ccxt.pro as ccxt
from typing import Optional
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass


class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class CCXTProStore(with_metaclass(MetaSingleton, object)):
    '''API provider for CCXT feed and broker classes.

    Added a new get_wallet_balance method. This will allow manual checking of the balance.
        The method will allow setting parameters. Useful for getting margin balances

    Added new private_end_point method to allow using any private non-unified end point

    '''

    # Supported granularities
    _GRANULARITIES = {
        (bt.TimeFrame.Minutes, 1): '1m',
        (bt.TimeFrame.Minutes, 3): '3m',
        (bt.TimeFrame.Minutes, 5): '5m',
        (bt.TimeFrame.Minutes, 15): '15m',
        (bt.TimeFrame.Minutes, 30): '30m',
        (bt.TimeFrame.Minutes, 60): '1h',
        (bt.TimeFrame.Minutes, 90): '90m',
        (bt.TimeFrame.Minutes, 120): '2h',
        (bt.TimeFrame.Minutes, 180): '3h',
        (bt.TimeFrame.Minutes, 240): '4h',
        (bt.TimeFrame.Minutes, 360): '6h',
        (bt.TimeFrame.Minutes, 480): '8h',
        (bt.TimeFrame.Minutes, 720): '12h',
        (bt.TimeFrame.Days, 1): '1d',
        (bt.TimeFrame.Days, 3): '3d',
        (bt.TimeFrame.Weeks, 1): '1w',
        (bt.TimeFrame.Weeks, 2): '2w',
        (bt.TimeFrame.Months, 1): '1M',
        (bt.TimeFrame.Months, 3): '3M',
        (bt.TimeFrame.Months, 6): '6M',
        (bt.TimeFrame.Years, 1): '1y',
    }

    BrokerCls = None  # broker class will auto register
    DataCls = None  # data class will auto register

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self, exchange, currency, config, retries, debug=False, sandbox=False):
        self.exchange = getattr(ccxt, exchange)(config)
        if sandbox:
            self.exchange.set_sandbox_mode(True)
        self.currency = currency
        self.retries = retries
        self.debug = debug
        self._cash = 0
        self._value = 0

    def get_granularity(self, timeframe, compression):
        if not self.exchange.has['fetchOHLCV']:
            raise NotImplementedError("'%s' exchange doesn't support fetching OHLCV data" % \
                                      self.exchange.name)

        granularity = self._GRANULARITIES.get((timeframe, compression))
        if granularity is None:
            raise ValueError("backtrader CCXT module doesn't support fetching OHLCV "
                             "data for time frame %s, comression %s" % \
                             (bt.TimeFrame.getname(timeframe), compression))

        if self.exchange.timeframes and granularity not in self.exchange.timeframes:
            raise ValueError("'%s' exchange doesn't support fetching OHLCV data for "
                             "%s time frame" % (self.exchange.name, granularity))

        return granularity

    async def get_balance(self, symbol=None, params={}):
        balance = await self.exchange.watch_balance(params)
        if symbol is None:
            symbol = self.currency
        cash = balance['free'][self.currency]
        if symbol in balance['total']:
            value = balance['total'][symbol]
        else:
            value = 0
        # Fix if None is returned
        self._cash = cash if cash else 0
        self._value = value if value else 0
        return self._cash, self._value

    async def get_positions(self, symbols=None, params={}):
        return await self.exchange.fetch_account_positions(symbols, params)

    async def create_order(self, symbol, order_type, side, amount, price, params):
        # returns the order
        return await self.exchange.create_order(symbol=symbol, type=order_type, side=side, amount=amount, price=price, params=params)

    async def cancel_order(self, order_id, symbol):
        return await self.exchange.cancel_order(order_id, symbol)

    async def fetch_trades(self, symbol, since: Optional[int] = None, limit: Optional[int] = None, params={}):
        return await self.exchange.watch_trades(symbol, since, limit, params)

    async def fetch_ohlcv(self, symbol, timeframe, since, limit, params={}):
        if self.debug:
            print('Fetching: {}, TF: {}, Since: {}, Limit: {}'.format(symbol, timeframe, since, limit))
        return await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit, params=params)

    async def watch_ohlcv(self, symbol, timeframe, since, limit, params={}):
        if self.debug:
            print('Fetching: {}, TF: {}, Since: {}, Limit: {}'.format(symbol, timeframe, since, limit))
        return await self.exchange.watch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit, params=params)

    async def fetch_order(self, oid, symbol, params={}):
        return await self.exchange.fetch_order(oid, symbol, params)

    async def fetch_open_orders(self, symbol=None):
        if symbol == None:
            return await self.exchange.fetch_open_orders()
        else:
            return await self.exchange.fetch_open_orders(symbol)

    async def private_end_point(self, type, endpoint, params):
        '''
        Open method to allow calls to be made to any private end point.
        See here: https://github.com/ccxt/ccxt/wiki/Manual#implicit-api-methods

        - type: String, 'Get', 'Post','Put' or 'Delete'.
        - endpoint = String containing the endpoint address eg. 'order/{id}/cancel'
        - Params: Dict: An implicit method takes a dictionary of parameters, sends
          the request to the exchange and returns an exchange-specific JSON
          result from the API as is, unparsed.

        To get a list of all available methods with an exchange instance,
        including implicit methods and unified methods you can simply do the
        following:

        print(dir(ccxt.hitbtc()))
        '''
        return await getattr(self.exchange, endpoint)(params)
