import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { placeTrade } from '../../store/portfolio/assets';
import './BuySellStock.css';

function BuySellStockForm({ symbol, buySell, hideForm, stock }) {
    const [count, setCount] = useState(0);
    const [cost, setCost] = useState(0);
    const [errors, setErrors] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const assets = useSelector(state => state.portfolio.assets);
    const bp = useSelector(state => state.portfolio.buying_power);
    const asset = Object.values(assets).find(a => a.symbol === symbol);
    const owned = asset ? asset.count : 0;

    const dispatch = useDispatch();

    useEffect(() => {
        const shares = Number(count);
        const total = shares * stock.current;
        const problems = [];
        if (buySell === 'sell' && shares > owned) {
            problems.push("You don't have that many shares to sell");
        }
        if (buySell === 'buy' && total > bp) {
            problems.push("You don't have enough buying power");
        }
        setCost(total.toFixed(2));
        setErrors(problems);
    }, [count, buySell, bp, stock, owned]);

    const handleChangeBuy = value => {
        const shares = Math.floor(Number(value));
        const affordable = Math.floor(bp / stock.current);
        if (!shares || shares < 1) setCount(affordable >= 1 ? 1 : 0);
        else if (shares > affordable) setCount(affordable);
        else setCount(shares);
    };

    const handleChangeSell = value => {
        const shares = Math.floor(Number(value));
        if (!shares || shares < 1) setCount(1);
        else if (shares > owned) setCount(owned);
        else setCount(shares);
    };

    const handleSubmit = async (e, side) => {
        e.preventDefault();
        if (errors.length || Number(count) < 1 || submitting) return;
        setSubmitting(true);
        const tradeErrors = await dispatch(placeTrade(symbol, side, count));
        setSubmitting(false);
        if (tradeErrors) {
            setErrors(tradeErrors);
            return;
        }
        setCount(0);
        hideForm();
    };

    return (
        <div className='buy-sell-stock-form-container'>
            {errors.map(error => (
                <div className='buy-sell-errors' key={error}>{error}</div>
            ))}
            {buySell === 'buy' && <div>{`Buy ${count} shares for ${Number(cost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`}</div>}
            {buySell === 'buy' && (
                <form className='buy-sell-form' onSubmit={e => handleSubmit(e, 'buy')}>
                    <input
                        type='number'
                        min='0'
                        step='1'
                        value={count}
                        onChange={e => handleChangeBuy(e.target.value)}
                    ></input>
                    <div className='buy-sell-btn-container'>
                        <button id="buy-btn" className='buy-sell-btn btn-filled' disabled={submitting}>Confirm Purchase</button>
                        <button id="cancel-btn" type="button" className='buy-sell-btn btn-filled' onClick={hideForm}>Cancel</button>
                    </div>
                </form>
            )}
            {buySell === 'sell' && asset && <div>{`Sell ${count} shares for ${Number(cost).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}`}</div>}
            {buySell === 'sell' && asset && (
                <form className='buy-sell-form' onSubmit={e => handleSubmit(e, 'sell')}>
                    <input type='number' min='1' step='1' value={count} onChange={e => handleChangeSell(e.target.value)} />
                    <div className='buy-sell-btn-container'>
                        <button id="buy-btn" className='buy-sell-btn btn-filled' disabled={submitting}>Confirm Sale</button>
                        <button id="cancel-btn" type="button" className='buy-sell-btn btn-filled' onClick={hideForm}>Cancel</button>
                    </div>
                </form>
            )}
            {/* <button onClick={hideForm}>Cancel</button> */}
        </div>
    );
}

export default BuySellStockForm;
