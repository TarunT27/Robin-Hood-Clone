import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Link } from 'react-router-dom';
import { deleteStockFromWatchlist } from '../../store/portfolio/watchlist';
import { formatPercent } from '../utils/stockUtils';
import WatchlistMenu from './watchlistMenu';
import './Watchlist.css';

function Watchlist({ watchlist, quotes }) {
  const dispatch = useDispatch();
  const [isOpen, setOpen] = useState(false);

  // Close the menu on any click elsewhere on the page.
  useEffect(() => {
    if (!isOpen) return;
    const closeMenu = () => setOpen(false);
    document.addEventListener('click', closeMenu);
    return () => document.removeEventListener('click', closeMenu);
  }, [isOpen]);

  return (
    <div className='watchListContainer'>
      <ul className='watchList'>
        <div className='nameAndMenuIcon stockSymbol'>
          <span id='watchlistNameMain'> {watchlist.name} </span>
          <span className={'menuSpan'} onClick={() => setOpen(!isOpen)}>
            {' '}
            {isOpen ? '-' : '+'}
            {isOpen && <WatchlistMenu watchlist={watchlist}></WatchlistMenu>}
          </span>
        </div>
        {watchlist &&
          Object.values(watchlist.stocks).map((stock, i) => (
            <div key={i} className={'outerDiv'}>
              <Link to={`/stocks/${stock.symbol}`}>
                <div className='watchlistStockContainer' key={i}>
                  <div className='leftSide'>
                    <span className='stockSymbol one'>{stock.symbol}</span>
                    <span
                      className='removeStockFromList stockSymbol'
                      onClick={async e => {
                        e.stopPropagation();
                        e.preventDefault();
                        await dispatch(deleteStockFromWatchlist(stock.id, watchlist));
                      }}
                    >
                      Remove
                    </span>
                  </div>
                  <div className='rightSide'>
                    <span className='stockPrice'>
                      {quotes[stock.symbol]?.current.toLocaleString('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      })}
                    </span>
                    <span
                      className={`stockChange ${
                        quotes[stock.symbol]?.change > 0 ? 'green' : 'red'
                      }`}
                    >
                      {formatPercent(quotes[stock.symbol]?.change_percent)}
                    </span>
                  </div>
                </div>
              </Link>
            </div>
          ))}
      </ul>
    </div>
  );
}

export default Watchlist;
