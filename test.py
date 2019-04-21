from requests import get, post, delete

print(delete('http://localhost:8080/news/30').json())  # Удаление новости
print(get('http://localhost:8080/news').json())  # Показать новости
print(get('http://localhost:8080/').json())  # Показать новости, но со "/"
print(get('http://localhost:8080/news/16').json())  # Показать новость
print(post('http://localhost:8080/news', json={"title": "Заголовок1", "content": "ЗРДАСССССЬЬ",
                                               "user_id": "5"}).json())  # Публикация новости
