import { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { Route } from 'react-router-dom';
import NavBar from './Navigation';
import { loadPortfolio } from '../store/portfolio';

const MainWrapper = props => {
  const dispatch = useDispatch();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      if (props.user) await dispatch(loadPortfolio());

      setLoaded(true);
    })();
    // Load once on mount; the user doesn't change while this page is open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch]);

  return (
    loaded && (
      <main>
        <Route {...props}>
          <NavBar user={props.user} />
          <div className='content'>{props.children}</div>
        </Route>
      </main>
    )
  );
};

export default MainWrapper;
