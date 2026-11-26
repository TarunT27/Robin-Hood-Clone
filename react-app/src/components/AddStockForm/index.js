import { useState } from 'react';
import { useDispatch} from 'react-redux';
import {
  addStockToWatchlist,
  searchStocks,
} from '../../store/portfolio/watchlist';
import { DebounceInput } from 'react-debounce-input';
import './addstockform.css';
const AddStockForm = ({ hideform, watchlist }) => {
  const dispatch = useDispatch();
  const [name, setName] = useState('');
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);

  const updateName = async e => {
    let str = e.target.value.trim();
    if (str !== '') {
      const res = await dispatch(searchStocks(str));
      setFilteredStocks(res || []);
    } else {
      setFilteredStocks([]);
    }
    setActiveSuggestionIndex(0);
    setShowSuggestions(true);
    setName(e.target.value);
  };
  // Adds the chosen stock by its symbol (the list shows "Name SYMBOL").
  const addStock = async stock => {
    if (!stock) return;
    setName(`${stock.name} ${stock.symbol}`);
    setFilteredStocks([]);
    const addedStock = await dispatch(addStockToWatchlist(stock.symbol, watchlist));
    if (addedStock && addedStock.error) {
      setValidationErrors([addedStock.error]);
    } else {
      setValidationErrors([]);
      setActiveSuggestionIndex(0);
      setShowSuggestions(false);
      hideform();
    }
  };

  const onSuggestion = index => async e => {
    e.preventDefault();
    await addStock(filteredStocks[index]);
  };

  const onKeyDown = async e => {
    if (e.keyCode === 13) {
      // console.log('IS THIS ENTER');
      e.preventDefault();
      if (filteredStocks.length !== 0) {
        await addStock(filteredStocks[activeSuggestionIndex]);
      }
    } else if (e.keyCode === 38) {
      if (activeSuggestionIndex === 0) {
        return;
      }
      setActiveSuggestionIndex(activeSuggestionIndex - 1);
    } else if (e.keyCode === 40) {
      if (activeSuggestionIndex >= filteredStocks.length - 1) {
        return;
      }
      setActiveSuggestionIndex(activeSuggestionIndex + 1);
    }
  };

  const SuggestionsList = () => {
    return filteredStocks.length ? (
      <ul className='suggestions'>
        {filteredStocks.map((suggestion, index) => {
          let className;
          // Flag the active suggestion with a class
          if (index === activeSuggestionIndex) {
            className = 'suggestion-active';
          }
          return (
            <li className={className} key={suggestion.symbol} onClick={onSuggestion(index)}>
              {`${suggestion.name} ${suggestion.symbol}`}
            </li>
          );
        })}
      </ul>
    ) : (
      <div className='no-suggestions'>
        <em>No suggestions</em>
      </div>
    );
  };

  let count = 0;
  return (
    <section>
      <div>
        {validationErrors.length > 0 && (
          <div className='errorsContainer'>
            {validationErrors.map(currError => {
              return <p key={`error-${count++}`}>{currError}</p>;
            })}
          </div>
        )}
        <label className='name'>
          Name
          <DebounceInput
            placeholder='search here...'
            minLength={2}
            debounceTimeout={500}
            onChange={event => updateName(event)}
            onKeyDown={onKeyDown}
            id={`input${watchlist.id}`}
          />
          {showSuggestions && name && (
            <SuggestionsList
              className='suggestions'
              filteredSuggestions={filteredStocks}
              onSuggestion={onSuggestion}
              activeSuggestionIndex={activeSuggestionIndex}
            />
          )}
        </label>
      </div>
    </section>
  );
};
export default AddStockForm;
