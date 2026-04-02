import sqlite3

class SQL:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    # Добавление пользователя в БД
    def add_user(self, id):
        query = "INSERT INTO users (id) VALUES(?)"
        with self.connection:
            return self.cursor.execute(query, (id,))

    # Проверка, есть ли пользователь в БД
    def user_exist(self, id):
        query = "SELECT * FROM users WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (id,)).fetchall()
            return bool(len(result))

    # Получить значение поля
    def get_field(self, table, id, field):
        query = f"SELECT {field} FROM {table} WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (id,)).fetchone()
            if result:
                return result[0]

    # Обновить значение поля
    def update_field(self, table, id, field, value):
        query = f"UPDATE {table} SET {field} = ? WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (value, id))


    #Таблица items
    def add_item(self, name, price):
        query = "INSERT INTO items (name, price) VALUES(?, ?)"
        with self.connection:
            self.cursor.execute(query, (name, price))

    def get_items_by_status(self, status):
        query = "SELECT * FROM items WHERE status = ?"
        with self.connection:
            return self.cursor.execute(query, (status,)).fetchall()

    def get_item_id(self, name):
        query = f"SELECT id FROM items WHERE name = ?"
        with self.connection:
            result = self.cursor.execute(query, (name,)).fetchone()
            if result:
                return result[0]
            else:
                return None
    #Таблица orders
    def add_order(self, user_id, item_id):
        query = "INSERT INTO orders (user_id, item_id) VALUES(?, ?)"
        with self.connection:
            self.cursor.execute(query, (user_id, item_id))

    def get_orders(self, user_id, status):
        query = """SELECT * FROM orders 
        JOIN items ON orders.item_id = items.id 
        WHERE orders.user_id = ? AND orders.status = ?
        """
        with self.connection:
            return self.cursor.execute(query, (user_id, status)).fetchall()

    def delete_order(self, user_id, item_id):
        query = "DELETE FROM orders WHERE user_id = ? AND item_id = ? AND status = 0"
        with self.connection:
            self.cursor.execute(query, (user_id, item_id))

    #получить количество товара в корзине
    def get_count(self, item_id, user_id, status):
        query = "SELECT count FROM orders WHERE item_id = ? AND user_id = ? AND status = ?"
        with self.connection:
            item = self.cursor.execute(query, (item_id, user_id, status)).fetchone()
            if item:
                return item[0]
            return 0

    #получить количество товара в корзине
    def get_order_id(self, item_id, user_id, status):
        query = "SELECT id FROM orders WHERE item_id = ? AND user_id = ? AND status = ?"
        with self.connection:
            item = self.cursor.execute(query, (item_id, user_id, status)).fetchone()
            if item:
                return item[0]
            return 0

    # Закрытие соединения
    def close(self):
        self.connection.close()
