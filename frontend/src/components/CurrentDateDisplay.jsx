import { useEffect, useState } from 'react';
import { CalendarDays } from 'lucide-react';

const formatLocalDate = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const CurrentDateDisplay = () => {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const updateDate = () => setNow(new Date());
    const delayToNextMinute = 60000 - (Date.now() % 60000) + 50;
    let intervalId;
    const initialTimeout = window.setTimeout(() => {
      updateDate();
      intervalId = window.setInterval(updateDate, 60000);
    }, delayToNextMinute);

    return () => {
      window.clearTimeout(initialTimeout);
      if (intervalId) window.clearInterval(intervalId);
    };
  }, []);

  const dateTime = formatLocalDate(now);
  const formattedDate = new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(now);

  return (
    <div className="current-date-display">
      <CalendarDays size={16} aria-hidden="true" />
      <span>
        <small>Today</small>
        <time dateTime={dateTime}>{formattedDate}</time>
      </span>
    </div>
  );
};

export default CurrentDateDisplay;
