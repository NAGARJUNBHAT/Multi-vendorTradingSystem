from flask import Blueprint, render_template, redirect, url_for, request, flash
import flask_login
from controller.database_controller import Database
from flask.json import jsonify

from blueprints.admin.forms.add_product import AddProductForm
from blueprints.admin.forms.add_shop import AddShopForm
from blueprints.admin.forms.update_product import UpdateProductForm
from blueprints.admin.forms.update_shop import UpdateShopForm
from utils import rand_id
import time
import os

database = Database.getInstance()

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/")
@flask_login.login_required
def home():
    if(flask_login.current_user.user_type == "customer"):
         return redirect(url_for("homepage"))

    username = flask_login.current_user.id
    shops = database.getAllShopsOfShopkeeper(username)
    orders = database.getAllOrdersOfShopkeeper(username)

    for order in orders:
        order["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(order.get("date_ordered"))))

    return render_template("admin.html", hide_admin_button=True, orders=orders, shops=shops, header_link=url_for("admin.home"))



@admin.route("/<shop_id>", methods = ['POST', 'GET'])
@flask_login.login_required
def view_shop(shop_id):
    if(flask_login.current_user.user_type == "customer"):
        return redirect(url_for("home"))
   
    (shop, products) = database.getShopDetails(shop_id) or (None, None)

    
    if shop is None:
        return redirect("admin.home")


    return render_template("admin-shop.html", hide_admin_button=True, shop=shop, products=products,  header_link=url_for("admin.home"))



@admin.route("/add-shop", methods=["GET", "POST"])
@flask_login.login_required
def new_shop():
    if(flask_login.current_user.user_type == "customer"):
         return redirect(url_for("home"))

    form = AddShopForm()
    if request.method == "GET":
        return render_template("admin-new-shop.html", hide_admin_button=True, form=form, header_link=url_for("admin.home"))
    elif request.method == "POST":
        if form.validate_on_submit():
           
            username = flask_login.current_user.id
            shopname = request.form.get("shop_name")
            shop_address= request.form.get("shop_address")
            shop_description = request.form.get("shop_description")
            shop_image = request.files.get("shop_image")
            shop_id = rand_id()

            filename = shop_id

            shop_image.save(os.path.join("shop_images", filename))
        
            database.createNewShop(username, shopname, shop_address, shop_description, shop_id)
            flash("Added new shop.")
            return redirect(url_for("admin.home"))
        
        return render_template("admin-new-shop.html", hide_admin_button=True, form=form)


@admin.route("/update-shop/<shop_id>", methods=["GET", "POST"])
@flask_login.login_required
def update_shop(shop_id):
    if(flask_login.current_user.user_type == "customer"):
         return redirect(url_for("home"))

    (shop, _) = database.getShopDetails(shop_id) or (None, None)

    if not shop:
        return redirect("admin.home")


    form = UpdateShopForm(data=shop)
    if request.method == "GET":
        return render_template("admin-update-shop.html", hide_admin_button=True, shop=shop, form=form, header_link=url_for("admin.home"))
    elif request.method == "POST":
        if form.validate_on_submit():
           
            username = flask_login.current_user.id
            shopname = request.form.get("shopname")
            shop_address= request.form.get("shop_address")
            shop_description = request.form.get("shop_description")
            shop_image = request.files.get("shop_image")

            filename = shop_id

            shop_image.save(os.path.join("shop_images", filename))
        
            database.updateShop(username, shopname, shop_address, shop_description, shop_id)
          
            flash("updated shop.")
            return redirect(url_for("admin.home"))
        
        return render_template("admin-new-shop.html", hide_admin_button=True, form=form)


@admin.route("/<shop_id>/add-product", methods=["GET", "POST"])
@flask_login.login_required
def new_product(shop_id):

    if(flask_login.current_user.user_type == "customer"):
        return redirect(url_for("home"))

    form = AddProductForm()

    (shop, _) = database.getShopDetails(shop_id) or (None, None)

    if shop is None:
        return redirect(url_for("admin.home"))

    if request.method == "GET":
        return render_template("admin-new-product.html", hide_admin_button=True, shop=shop, form=form, header_link=url_for("admin.home"))

    elif request.method == "POST":
        if form.validate_on_submit():
            product_id = rand_id()
            product_name = request.form.get("product_name")
            product_description = request.form.get("product_description")
            product_price = request.form.get("product_price")
            product_image = request.files.get("product_image")

            filename = product_id

            product_image.save(os.path.join("product_images", filename))

            database.addNewProduct(product_id,shop_id,product_name,product_description,product_price)
           
            flash("Added new product.")
            return redirect(url_for("admin.view_shop", shop_id=shop_id))
        
        return render_template("admin-new-product.html", hide_admin_button=True, shop=shop,  form=form)


@admin.route("/<shop_id>/<product_id>/update-product", methods=["GET", "POST"])
@flask_login.login_required
def update_product(shop_id, product_id):
    if(flask_login.current_user.user_type == "customer"):
         return redirect(url_for("home"))

    product = database.getProductDetails(product_id)

    if not product: 
        flash("Product not found!")
        return redirect("admin.home")

    form = UpdateProductForm(data=product)
    
    (shop, _) = database.getShopDetails(shop_id) or (None, None)

    if shop is None:
        flash("Shop not found!")
        return redirect("admin.home")

    if request.method == "GET":
        return render_template("admin-update-product.html", hide_admin_button=True, shop=shop, form=form, product=product, header_link=url_for("admin.home"))

    elif request.method == "POST":
        if form.validate_on_submit():
            product_id = product_id
            product_name = request.form.get("product_name")
            product_description = request.form.get("product_description")
            product_price = request.form.get("product_price")
            product_image = request.files.get("product_image")
            
            filename = product_id
            product_image.save(os.path.join("product_images", filename))
            
            database.updateProduct(product_name,product_description,product_price, product_id)
            
            flash("Updated new product.")
            return redirect(url_for("admin.view_shop", shop_id=shop_id))
        
        return render_template("admin-update-product.html", hide_admin_button=True, shop=shop, form=form, product=product, header_link=url_for("admin.home"))
        
@admin.route("/<shop_id>/<product_id>/remove-product", methods=["GET", "POST"])
@flask_login.login_required
def remove_product(shop_id, product_id):
    if(flask_login.current_user.user_type == "customer"):
        return redirect(url_for("home"))
    username = flask_login.current_user

    database.removeProduct(product_id)

    flash("Product Removed.")
    return redirect(url_for("admin.view_shop", shop_id=shop_id))

@admin.route("/order/<order_id>/", methods=["GET"])
@flask_login.login_required
def view_order(order_id):    
    if flask_login.current_user.user_type == "customer":
        return redirect(url_for("homepage"))
    else:     
        order = database.getOrderDetails(order_id)
        
        if not order:
            return redirect(url_for("admin.home"))
        order_items = database.getOrderItems(order_id)
        output = {}
        for i in order:
            output[i] = order[i]
        output["order_items"] = order_items
        order_total = 0
        for order_item in order_items:
            order_total += order_item.get("product_total")
        output["order_total"] = order_total
        output["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(output["date_ordered"])))
        #return jsonify(output)
        #return jsonify(order)
        return render_template("admin-order-view.html", order=output, hide_admin_button=True, header_link=url_for("admin.home")) 


@admin.route("/order/<order_id>/reject", methods=["GET"])
@flask_login.login_required
def reject_order(order_id):
    
    if flask_login.current_user.user_type == "customer":
        return redirect(url_for("homepage"))

    database.updateOrderStatus(order_id, "rejected")
    flash("Order Rejected!")

    return redirect(request.referrer)


@admin.route("/order/<order_id>/deliver", methods=["GET"])
@flask_login.login_required
def deliver_order(order_id):
    if flask_login.current_user.user_type == "customer":
        return redirect(url_for("homepage"))

    database.updateOrderStatus(order_id, "delivered")
    flash("Order Delivered!")

    # if flask_login.current_user.user_type == "shopkeeper":
    return redirect(request.referrer)

@admin.route("/order/<order_id>/accept", methods=["GET"])
@flask_login.login_required
def accept_order(order_id):
    if flask_login.current_user.user_type == "customer":
        return redirect(url_for("homepage"))

    database.updateOrderStatus(order_id, "accepted")
    flash("Order Accepted!")

    # if flask_login.current_user.user_type == "shopkeeper":
    return redirect(request.referrer)

@admin.route("/invoices")
@flask_login.login_required
def view_invoices():
    username = flask_login.current_user.id
    invoices = database.getInvoiceFromAllShopsOfShopkeeper(username)
    
    for invoice in invoices:
        invoice["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(invoice.get("date_ordered"))))

    return render_template("admin-view-invoices.html", invoices=invoices, hide_admin_button=True)

@admin.route("/invoice/<invoice_id>")
@flask_login.login_required
def view_invoice(invoice_id):
    
    (invoice, invoiceItems) = database.getInvoiceData(invoice_id) or (None, None)

    if not invoice:
        flash("Invalid invoice ID", "error")
        return redirect(url_for("admin.home"))
    
    invoice["date_ordered"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(invoice.get("date_ordered"))))

    

    return render_template("admin-view-invoice.html", invoice=invoice, invoiceItems=invoiceItems)