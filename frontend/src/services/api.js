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

export const searchTenders = async (query, regionCode = null, tenderCount = 10) => {
  try {
    // Очищаем запрос от кавычек и других проблемных символов
    const sanitizedQuery = sanitizeQueryString(query);
    
    console.log(`Отправка POST-запроса с запросом: ${sanitizedQuery}, регион: ${regionCode}, количество: ${tenderCount}`);
    
    // Формируем тело запроса
    const requestBody = {
      query: sanitizedQuery,
      top_k: tenderCount
    };
    
    // Добавляем код региона, если он задан
    if (regionCode) {
      requestBody.region = regionCode;
    }
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      throw new Error(`Ошибка сети: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Ответ API:', data);
    
    // Обработка данных
    if (!Array.isArray(data)) {
      console.error('API вернул не массив:', data);
      throw new Error('Неверный формат данных');
    }
    
    return data.map(tender => ({
      id: tender.id || tender.tender_id || "ИД-" + Math.random().toString(36).substr(2, 9),
      title: tender.name || tender.title || tender.description || "Тендер без названия",
      price: parseFloat(tender.price || tender.max_price || 0),
      date: tender.publish_date ? 
        new Date(tender.publish_date).toLocaleDateString('ru-RU') : 
        new Date().toLocaleDateString('ru-RU'),
      customer: tender.customer_name || tender.customer || "Неизвестный заказчик",
      region: tender.region || regionCode || null,
      score: tender.similarity_score !== undefined ? parseFloat(tender.similarity_score).toFixed(2) : null
    }));
    
  } catch (error) {
    console.error('Ошибка при получении данных:', error);
    // Возвращаем фиктивные данные для отображения
    return [
      {
        id: 'ERROR-001',
        title: `Не удалось получить данные: ${error.message}`,
        price: 0,
        date: new Date().toLocaleDateString('ru-RU'),
        customer: 'Ошибка API'
      }
    ];
  }
}; 