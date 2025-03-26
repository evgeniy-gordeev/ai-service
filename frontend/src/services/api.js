// В Docker контейнерах для общения между сервисами используем имя сервиса
const isDocker = process.env.REACT_APP_IN_DOCKER === 'true';

// Используем относительный URL для запросов через NGINX прокси
// Но для отладки оставляем возможность прямого доступа к API
const API_URL = process.env.NODE_ENV === 'production' || process.env.REACT_APP_USE_PROXY === 'true'
  ? '/search-tenders/' 
  : 'http://localhost:8001/search-tenders/';

/**
 * Очищает строку от кавычек и других потенциально опасных символов
 * @param {string} str - Исходная строка запроса
 * @return {string} - Очищенная строка
 */
const sanitizeQueryString = (str) => {
  if (!str) return '';
  
  // Удаляем кавычки (двойные и одинарные) и другие потенциально проблемные символы
  return str.replace(/['"\\]/g, '');
};

export const searchTenders = async (query, region, startDate, endDate) => {
  try {
    const response = await fetch(`${API_URL}/search-tenders/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        region,
        start_date: startDate,
        end_date: endDate,
      }),
    });

    if (!response.ok) {
      throw new Error('Ошибка при поиске тендеров');
    }

    const data = await response.json();
    console.log('API Response:', data);

    return data.tenders.map(tender => ({
      id: tender.id,
      name: tender.name,
      price: tender.price,
      customer: tender.customer_name,
      region: tender.region,
      publishDate: tender.publish_date,
      stage: tender.stage || "Не указан",
      score: tender.score || 0
    }));
  } catch (error) {
    console.error('Ошибка при поиске тендеров:', error);
    throw error;
  }
}; 