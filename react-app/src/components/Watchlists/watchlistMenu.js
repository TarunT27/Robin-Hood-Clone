import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import EditWatchlistForm from '../EditWatchlistForm';
import { deleteWatchlistReducer } from '../../store/portfolio/watchlist';

function WatchlistMenu({ watchlist }) {
  const dispatch = useDispatch();
  const [showEditModal, setShowEditModal] = useState(false);

  return (
    <div className='watchlistOptions' onClick={e => e.stopPropagation()}>
      <button
        className='editWatchlist'
        onClick={e => {
          e.preventDefault();
          setShowEditModal(true);
        }}
      >
        Edit
      </button>
      <button
        className='deleteWatchlist'
        onClick={() => dispatch(deleteWatchlistReducer(watchlist.id))}
      >
        Delete
      </button>
      {showEditModal && (
        <EditWatchlistForm
          watchlist={watchlist}
          showModal={showEditModal}
          setShowModal={setShowEditModal}
        />
      )}
    </div>
  );
}

export default WatchlistMenu;
