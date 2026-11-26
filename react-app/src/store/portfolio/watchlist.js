export const CREATE_WATCHLIST = 'watchlist/createWatchlist';
export const DELETE_WATCHLIST = 'watchlist/deleteWatchlist';
export const EDIT_WATCHLIST = 'watchlist/editWatchlist';

export const ADD_TO_WATCHLIST = 'watchlist/addToWatchlist';
export const DELETE_FROM_WATCHLIST = 'watchlist/deleteFromWatchlist';

const createWatchlistType = watchlist => {
  return {
    type: CREATE_WATCHLIST,
    payload: watchlist,
  };
};

const deleteWatchlistType = watchlist => {
  return {
    type: DELETE_WATCHLIST,
    payload: watchlist,
  };
};

const editWatchlistType = (watchlist, newName) => {
  return {
    type: EDIT_WATCHLIST,
    payload: watchlist,
    newName,
  };
};

const addToWatchlistType = (stock, watchlist) => {
  return {
    type: ADD_TO_WATCHLIST,
    stock,
    watchlist,
  };
};

const deleteFromWatchlistType = (stock, watchlist) => {
  return {
    type: DELETE_FROM_WATCHLIST,
    stock,
    watchlist,
  };
};

// Sends a request and returns [ok, data]. Errors come back as
// { error: 'message' } so the forms can show them.
const request = async (url, options = {}) => {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    });
  } catch (err) {
    return [false, { error: 'Could not reach the server. Please try again.' }];
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.error) {
    const error = data.error || (data.errors && data.errors[0]) || 'Something went wrong.';
    return [false, { error: String(error).replace(/^\w+ : /, '') }];
  }
  return [true, data];
};

export const searchStocks = query => async () => {
  const [ok, data] = await request(`/api/stocks/search/${encodeURIComponent(query)}`);
  return ok ? data : [];
};

export const createWatchlist = name => async dispatch => {
  const [ok, data] = await request('/api/portfolio/watchlists/', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
  if (ok) {
    data.stocks = data.stocks || {};
    await dispatch(createWatchlistType(data));
  }
  return data;
};

export const deleteWatchlistReducer = id => async dispatch => {
  const [ok, data] = await request(`/api/portfolio/watchlists/${id}`, { method: 'DELETE' });
  if (ok) await dispatch(deleteWatchlistType(data));
  return data;
};

export const editWatchlist = (name, userId, watchlistId) => async dispatch => {
  const [ok, data] = await request(`/api/portfolio/watchlists/${watchlistId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
  if (ok) await dispatch(editWatchlistType(data));
  return data;
};

export const addStockToWatchlist = (symbol, watchlist) => async dispatch => {
  const [ok, data] = await request(`/api/portfolio/watchlists/${watchlist.id}/stocks`, {
    method: 'POST',
    body: JSON.stringify({ symbol }),
  });
  if (ok) await dispatch(addToWatchlistType(data, watchlist));
  return data;
};

export const deleteStockFromWatchlist = (id, watchlist) => async dispatch => {
  const [ok, data] = await request(`/api/portfolio/watchlists/${watchlist.id}/stocks/${id}`, {
    method: 'DELETE',
  });
  if (ok) await dispatch(deleteFromWatchlistType(data, watchlist));
  return data;
};

let initialState = {};
const watchlistReducer = (state = initialState, action) => {
  let newState = {};
  switch (action.type) {
    case CREATE_WATCHLIST:
      // console.log('HITTING CREATE');
      newState = JSON.parse(JSON.stringify(state));
      newState.watchlists.push(action.payload);
      return newState;
    case DELETE_WATCHLIST:
      newState = JSON.parse(JSON.stringify(state));
      // need to find the watchlist that i deleted and remove it
      let watchlists = newState.watchlists;
      let index = -1;
      for (let i = 0; i < watchlists.length; i++) {
        let watchlist = watchlists[i];
        if (watchlist.id.toString() === action.payload.id.toString()) {
          // console.log('found deleted');
          index = i;
          break;
        }
      }
      watchlists.splice(index, 1);
      newState.watchlists = watchlists;
      return newState;
    case EDIT_WATCHLIST:
      newState = JSON.parse(JSON.stringify(state));
      let wLists = newState.watchlists;
      for (let wList of wLists) {
        if (action.payload.id.toString() === wList.id.toString()) {
          wList.name = action.payload.name;
        }
      }
      return newState;
    case ADD_TO_WATCHLIST:
      newState = JSON.parse(JSON.stringify(state));
      let lists = newState.watchlists;
      for (let list of lists) {
        if (action.watchlist.id.toString() === list.id.toString()) {
          list.stocks.push(action.stock);
        }
      }
      return newState;
    case DELETE_FROM_WATCHLIST:
      newState = JSON.parse(JSON.stringify(state));
      for (let list of newState.watchlists) {
        if (action.watchlist.id.toString() === list.id.toString()) {
          for (let x = 0; x < list.stocks.length; x++) {
            if (list.stocks[x].id === action.stock.id) {
              list.stocks.splice(x, 1);
            }
          }
        }
      }
      return newState;
    default:
      return state;
  }
};

export default watchlistReducer;
