const API_URL = 'http://localhost:8001'; // Адрес вашего API

export const searchTenders = async (query) => {
  try {
    const response = await fetch(`${API_URL}/search?query=${encodeURIComponent(query)}`);
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    const data = await response.json();
    
    // Преобразование данных из API в формат, понятный для компонентов
    return data.map(tender => ({
      id: tender.id,
      title: tender.name,
      price: tender.price,
      date: new Date(tender.publish_date).toLocaleDateString('ru-RU'),
      customer: tender.customer_name,
    }));
    
  } catch (error) {
    console.error('Error fetching tenders:', error);
    return [];
  }
}; 