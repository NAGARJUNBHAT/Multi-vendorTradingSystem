import calendar
from datetime import timezone, datetime
import mysql.connector
from utils import User
import bcrypt as bc
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

class Database:
    instance = None
    
    def tryConnect(self):
        print("Trying to connect")
        self.db = mysql.connector.connect(host="localhost", user="Arjun", password="arjun", database="project", )
        

    def __init__(self):
        if Database.instance == None:
            self.db = None  
            self.tryConnect()

            cursor = self.db.cursor()
            cursor.execute("""
            CREATE PROCEDURE IF NOT EXISTS checkuser(
                IN user VARCHAR(255),
                IN mail VARCHAR(255)
            )
            BEGIN
                SELECT username, email 
                FROM User
                WHERE username=user or email=mail;
            END
            """)


            cursor.execute("""
            CREATE TABLE IF NOT EXISTS User (
                    username varchar(30) NOT NULL,
                    password varchar(60) NOT NULL,
                    user_type varchar(10) NOT NULL,
                    email varchar(30) NOT NULL,
                    address varchar(130) NOT NULL,
                    PRIMARY KEY (username)
                );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop (
                username VARCHAR(30) NOT NULL,
                shopname VARCHAR(60) NOT NULL,
                shop_address VARCHAR(160) NOT NULL,
                shop_description VARCHAR(160) NOT NULL,
                shop_id VARCHAR(60) NOT NULL,
                PRIMARY KEY(shop_id),
                FOREIGN KEY(username) REFERENCES USER(username)
            )
            """)

            cursor.execute("""

            CREATE TABLE IF NOT EXISTS product (
                product_id VARCHAR(60) NOT NULL,
                shop_id VARCHAR(60) NOT NULL,
                product_name VARCHAR(60) NOT NULL,
                product_description VARCHAR(200) NOT NULL,
                product_price DOUBLE(10,2) NOT NULL,
                PRIMARY KEY (product_id),
                FOREIGN KEY (shop_id) REFERENCES shop (shop_id)
                ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                product_id VARCHAR(60) NOT NULL,
                username VARCHAR(60) NOT NULL,
                shop_id  VARCHAR(60) NOT NULL,
                quantity int(3) NOT NULL,
                FOREIGN KEY (username) REFERENCES user (username) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product (product_id) ON DELETE CASCADE,
                FOREIGN KEY (shop_id) REFERENCES shop (shop_id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_order (
                order_id  VARCHAR(60) NOT NULL,
                username VARCHAR(60) NOT NULL,
                shop_id  VARCHAR(60) NOT NULL,
                status  VARCHAR(60) NOT NULL,
                date_ordered  VARCHAR(60) NOT NULL,
                PRIMARY KEY (order_id),
                FOREIGN KEY (shop_id) REFERENCES shop (shop_id) ON DELETE CASCADE,
                FOREIGN KEY (username) REFERENCES user (username)
            )
            """)

            cursor.execute("""

            CREATE TABLE IF NOT EXISTS order_item (
                order_id  VARCHAR(60) NOT NULL,
                product_id VARCHAR(60) NOT NULL,
                quantity int(3) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES user_order (order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES product (product_id) ON DELETE CASCADE
            )

            """)

     
            cursor.execute("""

            CREATE TABLE IF NOT EXISTS invoice (
                invoice_id VARCHAR(60) NOT NULL,
                shop_id  VARCHAR(60) NOT NULL,
                order_id  VARCHAR(60) NOT NULL,
                customer_username VARCHAR(60) NOT NULL,
                customer_address VARCHAR(60) NOT NULL,
                order_total DOUBLE(10,2) NOT NULL,
                date_ordered VARCHAR(60) NOT NULL,
                PRIMARY KEY(invoice_id)
            )

            """)

            cursor.execute("""

            CREATE TABLE IF NOT EXISTS invoice_item (
                invoice_id VARCHAR(60) NOT NULL,
                product_name VARCHAR(60) NOT NULL,
                quantity int(3) NOT NULL,
                product_price DOUBLE(10,2) NOT NULL
            )

            """)

          
            cursor.execute("""

            CREATE TRIGGER IF NOT EXISTS generateInvoice
            AFTER UPDATE
            ON user_order FOR EACH ROW
            BEGIN
            

                IF old.status <> 'delivered' AND new.status = 'delivered'
                  THEN
                    SELECT LEFT(UUID(), 8) INTO @invoice_id;

                    SELECT SUM(order_item.quantity * product.product_price) 
                    INTO @order_total
                    FROM order_item
                    INNER JOIN product on product.product_id=order_item.product_id
                    WHERE order_item.order_id=new.order_id;

                    INSERT IGNORE INTO invoice(
                        invoice_id,
                        shop_id,
                        order_id,
                        customer_username,
                        customer_address,
                        order_total,
                        date_ordered
                    )
                    SELECT 
                    @invoice_id, 
                    new.shop_id,
                    new.order_id, 
                    user_order.username AS customer_username,
                    user.address AS customer_address,
                    @order_total,
                    new.date_ordered 
                    FROM user_order
                    INNER JOIN user on user.username=user_order.username
                    WHERE user_order.username=new.username;

                    INSERT INTO invoice_item(
                        invoice_id, 
                        product_name, 
                        quantity, 
                        product_price
                    )
                    SELECT @invoice_id,
                    product.product_name,
                    order_item.quantity,
                    product.product_price
                    FROM order_item 
                    INNER JOIN product on product.product_id=order_item.product_id
                    WHERE order_item.order_id=new.order_id;
                END IF;
            END

            """)

            cursor.close()
            Database.instance = self


    @staticmethod 
    def getInstance():
        if Database.instance == None:
            return Database()
        else:
            return Database.instance
    
    def getUser(self, username):
        cur = self.db.cursor(dictionary=True)
        query = "SELECT * FROM User WHERE username = %s"
        cur.execute(query, (username, ))
        found_user = cur.fetchall()
        cur.close()

        if found_user == []:
            return
        else:
            user = User()
            user.id =found_user[0]["username"]
            user.username =found_user[0]["username"]
            user.user_type =found_user[0]["user_type"]
            return user
    
    def loadUser(self, username):
        if username == None: 
            return
        cur = self.db.cursor(dictionary=True)
        query = "SELECT * FROM User WHERE username = %s"
        cur.execute(query, (username, ))
        found_user = cur.fetchall()
        cur.close()
        if found_user == []:
            return
        else:

            user = User()
            user.username = username
            return user
    

    def authenticateUser(self, username, password):
        cur = self.db.cursor(dictionary=True)
        query = "SELECT * FROM User WHERE username = %s"
        adr = username.strip()
        cur.execute(query, (adr, ))
        found_user = cur.fetchall()
        cur.close()
        if found_user == []:
            return None
        else:
            if bcrypt.check_password_hash(found_user[0]["password"], password):
               return found_user[0]
            else: return None


    def checkUserExists(self, username, email):  
        cursor = self.db.cursor(dictionary=True)
        cursor.callproc( "checkuser", (username, email) )
        result = None
        for res in cursor.stored_results():
            result = res.fetchone()
        cursor.close()
        return result

    def registerUser(self, username, password, user_type, email, address):
        cur = self.db.cursor() 
        pwhash = bc.hashpw(password.encode('utf-8'), bc.gensalt())
        password_hash = pwhash.decode('utf-8') 
        sql = "INSERT INTO User (username, password, user_type, email, address) VALUES (%s, %s, %s, %s, %s)"
        val = (username, password_hash, user_type, email, address)
        cur.execute(sql, val)
        self.db.commit() 
        cur.close()

    def getAllShops(self):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM shop"
        cur.execute(query)
        shops = cur.fetchall()
        cur.close()
        return shops

    def getShopDetails(self, shop_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM shop WHERE shop_id=%s"
        cur.execute(query, (shop_id, ))
        shop = cur.fetchone()

        query = "SELECT product_id, shop_id, product_name, product_description, product_price FROM product WHERE shop_id=%s"
        cur.execute(query, (shop_id, ))
        products = cur.fetchall()
        cur.close()
        return (shop, products)

    def getProductDetails(self, product_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM product WHERE product_id=%s"
        cur.execute(query, (product_id, ))
        product = cur.fetchone()
        cur.close()
        return product



    def getAllShopsOfShopkeeper(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM shop WHERE username=%s"
        cur.execute(query, (username, ))
        shops = cur.fetchall()
        cur.close()
        return shops

    def getAllOrdersOfShopkeeper(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        sql = """SELECT * FROM user_order
        INNER JOIN shop ON shop.shop_id=user_order.shop_id
        WHERE user_order.shop_id IN (SELECT shop_id from shop WHERE username=%s)
        """
        vals = (username, )
        cur.execute(sql, vals)
        orders = cur.fetchall()
        cur.close()
        return orders

    def getAllOrdersOfUser(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        sql = """
        SELECT * FROM user_order
        INNER JOIN shop ON shop.shop_id=user_order.shop_id
        WHERE user_order.username=%s
        """
        vals = (username, )
        cur.execute(sql, vals)
        orders = cur.fetchall()
        cur.close()
        return orders
                
    def getOrderDetails(self, order_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """
        SELECT user_order.shop_id, user_order.date_ordered,user.address,user_order.order_id, shopname, status, user.username from user_order 
        INNER JOIN shop on shop.shop_id=user_order.shop_id
        INNER JOIN user on user.username=user_order.username
        WHERE user_order.order_id=%s
        """
        cur.execute(query, (order_id, ))
        order = cur.fetchone()
        cur.close()
        return order

    def getOrderItems(self, order_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """
        SELECT *, order_item.quantity*product.product_price AS product_total from order_item 
        INNER JOIN product on product.product_id=order_item.product_id
        WHERE order_id=%s
        """
        cur.execute(query, (order_id, ))
        order_items = cur.fetchall()
        cur.close()
        return order_items

    def createNewShop(self, username, shopname, shop_address, shop_description, shop_id):
        query = """
        INSERT INTO shop (username, shopname, shop_address, shop_description, shop_id)
            values (%s, %s, %s, %s, %s) 
        """
        cur = self.db.cursor(buffered=True)
        cur.execute(query, (
            username,
            shopname,
            shop_address,
            shop_description,
        shop_id, 
        ))
        self.db.commit()
        cur.close()

    def updateShop(self, username, shopname, shop_address, shop_description, shop_id):
        query = """
        UPDATE shop set shopname=%s, shop_address=%s, shop_description=%s
            where username=%s and shop_id=%s
        """
        cur = self.db.cursor(buffered=True)
        cur.execute(query, (
            shopname,
            shop_address,
            shop_description,
            username,
            shop_id, 
        ))
        self.db.commit()
        cur.close()

    def addNewProduct(self, product_id,shop_id,product_name,product_description,product_price):
        cur = self.db.cursor(buffered=True)
        sql = """INSERT INTO product (product_id,shop_id,product_name, product_description,product_price)
                 values (%s, %s, %s, %s, %s)"""
        cur.execute(sql, (product_id,shop_id,product_name,product_description,product_price))
        self.db.commit()
        cur.close()


    def updateProduct(self,product_name,product_description,product_price, product_id):
        cur = self.db.cursor(buffered=True)
        sql = """
            UPDATE product 
            set product_name=%s, product_description=%s, product_price=%s
            WHERE product_id=%s
        """
        cur.execute(sql, (product_name,product_description,product_price, product_id))
        self.db.commit()
        cur.close()


    def updateOrderStatus(self, order_id, status):
        cur = self.db.cursor(buffered=True)
        query = """
            UPDATE user_order
            set status=%s
            WHERE order_id=%s
        """
        ok = cur.execute(query, (status, order_id, ))
        self.db.commit()
        cur.close()

    def getProductsInCart(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """
            SELECT 
            cart.product_id,
            cart.username,
            cart.shop_id,
            cart.quantity,
            shop.shopname,
            shop.shop_address,
            shop.shop_description,    
            product.product_name,
            product.product_description,
            product.product_price,   
            cart.quantity*product.product_price AS product_total

            FROM cart
            inner join shop ON shop.shop_id=cart.shop_id
            inner join product on product.product_id=cart.product_id
            WHERE cart.username=%s
        """
        cur.execute(query, (username, ))
        products = cur.fetchall()
        cur.close()
        return products

    def fetchProductInCart(self, username, product_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM cart WHERE username=%s and product_id=%s"
        cur.execute(query, (username, product_id ))
        products = cur.fetchall()
        cur.close()
        return products

    def fetchProductsOfShopInCart(self, shop_id, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "SELECT * FROM cart WHERE shop_id=%s and username=%s"
        cur.execute(query, (shop_id, username))
        shop_products = cur.fetchall()
        cur.close()
        return shop_products

    def addProductToCart(self, product_id, username, shop_id, quantity):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "INSERT INTO cart (product_id, username, shop_id, quantity) values (%s, %s, %s, %s) "
        cur.execute(query, (product_id, username, shop_id, quantity,  ))
        self.db.commit()
        cur.close()

    def updateProductInCart(self, quantity, product_id, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = "UPDATE cart SET quantity=%s WHERE product_id=%s AND username=%s"
        cur.execute(query, (quantity, product_id, username, ))
        self.db.commit()
        cur.close()

    def removeProductFromCart(self, product_id, username):
        cur = self.db.cursor(buffered=True)
        query = "DELETE FROM cart WHERE product_id=%s AND username=%s"
        cur.execute(query, (product_id, username))
        self.db.commit()
        cur.close()
    
    def clearShopCartOfUser(self, username, shop_id):
        cur = self.db.cursor(buffered=True)
        query = "DELETE FROM cart WHERE username=%s and shop_id=%s"
        cur.execute(query, (username,shop_id))
        self.db.commit()
        cur.close()

    def placeOrders(self, username, orders):
        cur = self.db.cursor(buffered=True)
        sql = """INSERT INTO user_order (order_id, username, shop_id, status, date_ordered) values(%s, %s, %s, %s, %s)"""

        vals = []

        for order_id in orders:
            vals.append((order_id, username, orders[order_id].get("shop_id"), "processing", calendar.timegm(datetime.utcnow().utctimetuple())    ))
         
        cur.executemany(sql, vals)
        self.db.commit()
     

        sql = """DELETE from cart WHERE username=%s"""
        vals = (username, )
        cur.execute(sql, vals)
        self.db.commit()
      

        sql = """INSERT INTO order_item (order_id, product_id, quantity) values(%s, %s, %s)"""

        vals = []
        for order_id in orders:
            for prod in orders[order_id].get("order_items"):
                vals.append((order_id, prod.get("product_id"), prod.get("quantity")))
        
        cur.executemany(sql, vals)
        self.db.commit()
        cur.close()

    def removeProduct(self, product_id):
        cur = self.db.cursor(buffered=True)
        sql = "DELETE FROM order_item where product_id=%s"
        cur.execute(sql, (product_id, ))
        self.db.commit()
        cur.close()
  
        sql = "DELETE FROM cart where product_id=%s"
        cur.execute(sql, (product_id, ))
        self.db.commit()
        cur.close()

        sql = "DELETE FROM product where product_id=%s"
        cur.execute(sql, (product_id, ))
        self.db.commit()
        cur.close()


    def getInvoiceFromAllShopsOfShopkeeper(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """SELECT * FROM invoice  INNER JOIN shop on shop.shop_id=invoice.shop_id
         where invoice.shop_id IN (SELECT shop_id from shop where username = %s) 
        """
        cur.execute(query, (username, ))
        invoices = cur.fetchall()
        cur.close()
        return invoices
    
    def getInvoicesOfUser(self, username):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """SELECT * FROM invoice  INNER JOIN shop on shop.shop_id=invoice.shop_id
         where customer_username = %s
        """
        cur.execute(query, (username, ))
        invoices = cur.fetchall()
        cur.close()
        return invoices

    def getInvoiceData(self, invoice_id):
        cur = self.db.cursor(dictionary=True, buffered=True)
        query = """SELECT * FROM invoice  INNER JOIN shop on shop.shop_id=invoice.shop_id
         where invoice_id=%s 
        """
        cur.execute(query, (invoice_id, ))
        invoice = cur.fetchone()

        query = """SELECT * FROM invoice_item where invoice_id=%s 
        """
        cur.execute(query, (invoice_id, ))
        invoiceItems = cur.fetchall()
        
        cur.close()
        return (invoice, invoiceItems)