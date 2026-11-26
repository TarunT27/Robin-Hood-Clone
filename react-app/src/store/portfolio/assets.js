import { ADD_BP } from './buyingPower';

export const TRADE_ASSETS = '/portfolio/assets/TRADE';
export const SELL_ALL_ASSETS = '/portfolio/assets/SELL_ALL';

const trade = asset => ({
  type: TRADE_ASSETS,
  asset,
});

const sellAll = symbol => ({
  type: SELL_ALL_ASSETS,
  symbol,
});

const setBuyingPower = bp => ({
  type: ADD_BP,
  payload: bp,
});

/**
 * Buys or sells shares at the current market price. The server prices the
 * trade and updates buying power and the holding together.
 *
 * Resolves to null on success, or to a list of error messages.
 */
export const placeTrade = (symbol, side, count) => async dispatch => {
  let response;
  try {
    response = await fetch('/api/portfolio/assets/trade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, side, count: Number(count) }),
    });
  } catch (err) {
    return ['Could not reach the server. Please try again.'];
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    return data.errors || ['An error occurred. Please try again.'];
  }

  if (data.asset) dispatch(trade(data.asset));
  else dispatch(sellAll(data.symbol));
  dispatch(setBuyingPower(data.buying_power));
  return null;
};

const initialState = {};

export default function assetReducer(state = initialState, action) {
  switch (action.type) {
    case TRADE_ASSETS:
      return { ...state, [action.asset.symbol]: action.asset };
    case SELL_ALL_ASSETS: {
      const newState = { ...state };
      delete newState[action.symbol];
      return newState;
    }
    default:
      return state;
  }
}
