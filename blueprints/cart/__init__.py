from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from controller.database_controller import Database
import flask_login
from flask.helpers import flash
from utils import rand_id
import time

database = Database.getInstance()


cart = Blueprint("cart", __name__, template_folder="templates")

@cart.route("/", methods=["GET", "POST"])
@flask_login.login_required
def home():
    if flask_login.current_user.user_type == "shopkeeper":
        return redirect(url_for("admin.home"))
    username = flask_login.current_user.id
 
    products = database.getProductsInCart(username)

    total_price=0

    for product in products:
        total_price += product.get("quantity") * product.get("product_price")
    
    if request.method=="POST":
        return jsonify({"total_price":total_price})

    return render_template("cart.html", cart=products, total_price=total_price)

@cart.route("/add/", methods=["GET","POST"])
@flask_login.login_required
def add_to_cart():
    try:
        if request.method == "GET":
            return redirect(url_for("homepage"))

        username = flask_login.current_user.id
        product_id = request.json.get("product_id")
        shop_id = request.json.get("shop_id")
        quantity = int(request.json.get("quantity"))

        

        products = database.fetchProductInCart(username, product_id)
        if not products: 
            database.addProductToCart(product_id, username, shop_id, quantity)
            return jsonify({
                "status":"success",
                "message":"Added to cart."
            })

        else:
            database.updateProductInCart(quantity, product_id, username)
            return jsonify({
                "status":"success",
                "message":"updated item in cart."
            })
    except:
        return jsonify({
            "status":"error",
            "message":"something went wrong!"
        })
    

@cart.route("/remove/", methods=["GET","POST"])
@flask_login.login_required
def remove_from_cart():
        if request.method == "GET":
            return redirect(url_for("homepage"))
        database.removeProductFromCart(request.form.get("product_id"), flask_login.current_user.id)
        flash("removed item from cart.")
        return redirect(request.referrer)
    

@cart.route("/placeorder/", methods=["GET","POST"])
@flask_login.login_required
def place_order():
    if request.method == "GET":
        return redirect(url_for("home"))
        
    username = flask_login.current_user.id
    
    cart_products = database.getProductsInCart(username)

    split_by_shop = {}

    for product in cart_products:
        if product.get("shop_id") in split_by_shop: 
            split_by_shop[product.get("shop_id")].append(product)
        else:
            split_by_shop[product.get("shop_id")] = [product]

    orders = {}


    for k in split_by_shop:
        orders[rand_id()] = {
            "shop_id": k,
            "order_items": split_by_shop[k]
        }

    
    database.placeOrders(username, orders)  
    flash("Your order has been placed!", "success")

    return jsonify({
        "status":"success",
        "message":"Your order has been placed!"
    })


@cart.route("/clearcart/", methods=["GET","POST"])
@flask_login.login_required
def clear_cart():
    if request.method == "GET":
        return redirect(url_for("homepage"))
        
    shop_id = request.form.get("shop_id")
    username = flask_login.current_user.id
    database.clearShopCartOfUser(username, shop_id)
    flash("Cancelled order.")
    return redirect(url_for("cart.home"))