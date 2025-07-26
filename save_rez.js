router.post('/api/save-test-result', async (req, res) => {
  if (!req.session.user || !req.session.user.isAuthenticated) {
    return res.status(401).json({ error: 'Необходима авторизация' });
  }

  const { nature, tech, people, signs, art } = req.body;
  const userId = req.session.user.id;
  
  // Определяем доминирующий тип
  const scores = {
    'Человек-природа': nature,
    'Человек-техника': tech,
    'Человек-человек': people,
    'Человек-знаковая система': signs,
    'Человек-художественный образ': art
  };
  
  const dominantType = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);

  try {
    await pool.query(
      `INSERT INTO test_results 
       (user_id, nature_score, tech_score, people_score, signs_score, art_score, dominant_type)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [userId, nature, tech, people, signs, art, dominantType]
    );
    
    res.json({ success: true });
  } catch (error) {
    console.error('Ошибка сохранения результатов:', error);
    res.status(500).json({ error: 'Произошла ошибка при сохранении результатов' });
  }
});