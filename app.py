from flask import Flask, render_template, redirect, request
from flask.helpers import flash, send_from_directory, url_for

import flask_login

from blueprints.cart import cart
from blueprints.admin import admin
from controller.database_controller import Database

from forms.registration_form import RegistrationForm
from forms.login_form import LoginForm
from utils import User
from flask.json import jsonify
import time


login_manager = flask_login.LoginManager()

app = Flask(__name__)
app.secret_key = 'super secret string'
app.config['SECRET_KEY'] = 'okokokok'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

database = Database.getInstance()

@app.before_request
def before_request_callback():
    if not database.db.is_connected():
        database.tryConnect()


login_manager.init_app(app)



@login_manager.user_loader
def user_loader(username):
   return database.getUser(username)
   


@login_manager.request_loader
def request_loader(request):
    return database.loadUser(request.form.get("username"))



app.register_blueprint(cart, url_prefix="/cart")
app.register_blueprint(admin, url_prefix="/admin")


@app.route("/")
def homepage():
    shops = database.getAllShops()
    return render_template("home.html", shops=shops, is_shopkeeper=flask_login.current_user.is_authenticated and flask_login.current_user.user_type == "shopkeeper")

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()

    if request.method == "POST": 
        if form.validate_on_submit():
            username = request.form.get("username")
            password = request.form.get("password")
            remember_me = request.form.get("remember_me")
 

            auth_user = database.authenticateUser(username, password)
            if auth_user is None:
                    flash("Invalid username or password!","error")
            else:
                user = User()
                user.id = auth_user["username"]
                user.username = auth_user["username"]
                user.user_type = auth_user["user_type"]
                flask_login.login_user(user, remember=remember_me == "y")
                
                if auth_user["user_type"] == "shopkeeper":
                    return redirect(url_for('admin.home'))
                elif auth_user["user_type"] == "customer":
                    return redirect(url_for('homepage'))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for("homepage"))


@app.route("/register", methods=["GET", "POST"])
def registration():
    form = RegistrationForm()
    if request.method == 'GET':
        return render_template("register.html", form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():

            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            user_type = request.form["user_type"]
            address = request.form["address"]
            
            result = database.checkUserExists(username, email)

            if result != None:
                if result[0] == username:
                    flash("Username already exists!", "error")

                if result[1] == email:
                    flash("Email already exists!", "error")
                
                return redirect(url_for("registration"))
            
            else:
              
                database.registerUser(username, password, user_type, email, address)

                flash("Registered successfully, please login!", "registration_success")
                return redirect(url_for("login"))

        return render_template("register.html", form=form)
        



@app.route("/shop/<shop_id>")
def shoproute(shop_id):

    (shop, products) = database.getShopDetails(shop_id) or (None, None)

    if shop is None:
        flash(jsonify({ "status": "error", "message": "Shop doesn't exist!!" }))
        return redirect("homepage")

    return render_template("shop.html",
        title=shop.get("shopname"),
        products=products,
        shop_id=shop_id, 
        shop=shop,
        is_shopkeeper=flask_login.current_user.is_authenticated and flask_login.current_user.user_type == "shopkeeper"
    )

@app.route("/product-img/<product_id>")
def product_image(product_id):
    return send_from_directory("product_images",
                               product_id)

@app.route("/shop-img/<shop_id>")
def shop_image(shop_id):
    return send_from_directory("shop_images",
                               shop_id)

@app.route("/my-orders/", methods=["GET"])
@flask_login.login_required
def my_orders():

    if flask_login.current_user.user_type == "shopkeeper":
        return redirect(url_for("admin.home"))

    username = flask_login.current_user.id
    orders = database.getAllOrdersOfUser(username)

    for order in orders:        
        order["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(order.get("date_ordered"))))

    output = []
    for order in orders:
        if order.get("status") == "processing":
            output.insert(0,order)
        else:
            output.insert( len(output) , order)
    return render_template("my-orders.html", orders=output)



@app.route("/order/<order_id>/", methods=["GET"])
@flask_login.login_required
def order_view(order_id):
    

    order = database.getOrderDetails(order_id)

    if not order:
        flash("Order doesnt exist!")
        return redirect(url_for("homepage"))

    if flask_login.current_user.user_type == "shopkeeper":
        return redirect(url_for("admin.view_order", order_id=order_id))

    else:

        order_items = database.getOrderItems(order_id)
        output = {}
        for i in order:
            output[i] = order[i]
        output["order_items"] = order_items
        order_total = 0
        for order_item in order_items:
            order_total += order_item.get("product_total")
        output["order_total"] = order_total
       
        return render_template("order-view.html", order=output)   

@app.route("/order/<order_id>/cancel/", methods=["GET","POST"])
@flask_login.login_required
def order_cancel(order_id):
    database.updateOrderStatus(order_id,"cancelled")
    flash("Order cancelled.")
    return redirect(request.referrer)


@app.route("/invoices")
@flask_login.login_required
def view_my_invoices():
    username = flask_login.current_user.id
    invoices = database.getInvoicesOfUser(username)
    return render_template("my-invoices.html", invoices=invoices)


@app.route("/invoice/<invoice_id>", methods=["GET"])
@flask_login.login_required
def view_invoice_details(invoice_id):
    
    (invoice, invoiceItems) = database.getInvoiceData(invoice_id) or (None, None)

    if not invoice:
        flash("Invalid invoice ID", "error")
        return redirect(url_for("homepage"))
    
    invoice["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(invoice.get("date_ordered"))))

    return render_template("view-invoice-details.html", invoice=invoice, invoiceItems=invoiceItems)


@app.errorhandler(404)
def page_not_found(e):
    return "Error 404 not found", 404


@login_manager.unauthorized_handler
def unauthorized_handler():
    if request.method == "GET":
        return redirect(url_for("login"))
    else:
        return jsonify({
            "status":"error",
            "message":"please login first!",
        })
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")