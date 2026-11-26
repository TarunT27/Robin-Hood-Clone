import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import CreateWatchlistForm from '../CreateWatchlistform';
import Watchlist from './Watchlist';
import 'react-tabs/style/react-tabs.css';
import './Watchlist.css';

const WatchlistList = ({ quotes }) => {
  const [showModal, setShowModal] = useState(false);
  const [showCreateWatchlistForm, changeCreateWatchlistForm] = useState(true);

  const watchlists = Object.values(useSelector(state => state.portfolio.watchlists));

  const toggleCreateWatchlistForm = () => {
    setShowModal(true);
    changeCreateWatchlistForm(!showCreateWatchlistForm);
  };

  return (
    <div className='watchlistListContainer'>
      <div>
        <button className='createWatchlistButton' onClick={toggleCreateWatchlistForm}>
          New Watchlist
        </button>
        {showModal && (
          <CreateWatchlistForm
            hideform={toggleCreateWatchlistForm}
            showModal={showModal}
            setShowModal={setShowModal}
          />
        )}
      </div>

      {watchlists.map(watchlist => (
        <div
          key={'watchlist' + watchlist.id}
          className='notActiveWatchlist watchlist'
          onClick={event => {
            // Clicking the list (not its buttons) expands or collapses it.
            if (event.target.tagName !== 'BUTTON' && event.target.tagName !== 'SPAN') {
              event.currentTarget.classList.toggle('activeWatchlist');
            }
          }}
        >
          <div className='flexDiv'>
            <Watchlist watchlist={watchlist} quotes={quotes} />
          </div>
        </div>
      ))}
    </div>
  );
};

export default WatchlistList;
