export const ADD_BP = 'buying_power/ADD';

const add = bp => ({
  type: ADD_BP,
  payload: bp,
});

/**
 * Moves pretend money from a linked bank account into buying power.
 * Buying power is only ever spent through a trade (see assets.js).
 */
export const addBuyingPower = bp => async dispatch => {
  const response = await fetch('/api/portfolio/buying-power/add', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      buying_power: Number(bp),
    }),
  });

  if (response.ok) {
    const bp = await response.json();
    dispatch(add(Number(bp)));
    return null;
  } else if (response.status < 500) {
    const data = await response.json();
    if (data.errors) {
      return data.errors;
    }
  }
  return ['An error occurred. Please try again.'];
};

export default function bpReducer(state = null, action) {
  switch (action.type) {
    case ADD_BP:
      return action.payload;
    default:
      return state;
  }
}
