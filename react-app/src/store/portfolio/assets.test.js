import assetReducer, { placeTrade, TRADE_ASSETS, SELL_ALL_ASSETS } from './assets';
import { ADD_BP } from './buyingPower';
import portfolioReducer from './index';

const mockFetch = (status, body) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) })
  );
};

afterEach(() => {
  delete global.fetch;
});

describe('placeTrade', () => {
  it('posts the trade and updates the holding and buying power', async () => {
    mockFetch(200, {
      symbol: 'AAPL',
      asset: { id: 1, symbol: 'AAPL', count: 3 },
      buying_power: 970,
    });
    const dispatch = jest.fn();

    const result = await placeTrade('AAPL', 'buy', '3')(dispatch);

    expect(result).toBeNull();
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toBe('/api/portfolio/assets/trade');
    expect(JSON.parse(options.body)).toEqual({ symbol: 'AAPL', side: 'buy', count: 3 });
    expect(dispatch).toHaveBeenCalledWith({
      type: TRADE_ASSETS,
      asset: { id: 1, symbol: 'AAPL', count: 3 },
    });
    expect(dispatch).toHaveBeenCalledWith({ type: ADD_BP, payload: 970 });
  });

  it('removes the holding when everything is sold', async () => {
    mockFetch(200, { symbol: 'AAPL', asset: null, buying_power: 1000 });
    const dispatch = jest.fn();
    await placeTrade('AAPL', 'sell', 3)(dispatch);
    expect(dispatch).toHaveBeenCalledWith({ type: SELL_ALL_ASSETS, symbol: 'AAPL' });
  });

  it('returns the server errors and changes nothing', async () => {
    mockFetch(400, { errors: ["You don't have enough buying power."] });
    const dispatch = jest.fn();
    const result = await placeTrade('AAPL', 'buy', 999)(dispatch);
    expect(result).toEqual(["You don't have enough buying power."]);
    expect(dispatch).not.toHaveBeenCalled();
  });

  it('reports network failures', async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error('offline')));
    const result = await placeTrade('AAPL', 'buy', 1)(jest.fn());
    expect(result[0]).toMatch(/server/);
  });
});

describe('reducers', () => {
  const portfolio = {
    buying_power: 100,
    assets: { AAPL: { id: 1, symbol: 'AAPL', count: 2 } },
    bank_accounts: {},
    watchlists: {},
  };

  it('does not mutate the previous portfolio state', () => {
    const next = portfolioReducer(portfolio, {
      type: TRADE_ASSETS,
      asset: { id: 1, symbol: 'AAPL', count: 5 },
    });
    expect(next.assets.AAPL.count).toBe(5);
    expect(portfolio.assets.AAPL.count).toBe(2);
  });

  it('removes sold-out holdings', () => {
    const next = portfolioReducer(portfolio, { type: SELL_ALL_ASSETS, symbol: 'AAPL' });
    expect(next.assets).toEqual({});
    expect(portfolio.assets.AAPL).toBeDefined();
  });

  it('asset reducer adds and removes', () => {
    let state = assetReducer({}, { type: TRADE_ASSETS, asset: { symbol: 'MSFT', count: 1 } });
    expect(state.MSFT.count).toBe(1);
    state = assetReducer(state, { type: SELL_ALL_ASSETS, symbol: 'MSFT' });
    expect(state).toEqual({});
  });
});
