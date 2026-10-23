import express from 'express';

const app = express();

app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Backend is running',
  });
});

export default app;