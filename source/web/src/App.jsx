import { useEffect, useState } from 'react';

function App() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error('API request failed');
        }

        return response.json();
      })
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main>
      <h1>Codepath</h1>

      {health && <p>{health.message}</p>}
      {error && <p>Backend error: {error}</p>}
    </main>
  );
}

export default App;