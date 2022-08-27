# Utils
from numpy import sin, cos, arccos, pi, round
from datetime import datetime, timedelta
import decimal
from regex import R

# Bot
import telebot
from telebot import types

# URLS
import urllib
import sys

# Database
import mariadb

import pandas as pd


print("Initializing configurations...")

# Latitud: 19.455698. Longitud: -70.696685

TLAT = 19.450696
TLON = -70.695029

# Utils

cart = []
#

user_dict = {}

user_cart_dict = {}


class UserCart:
    def __init__(self, name):
        self.name = name
        self.cart = []


class User:
    def __init__(self, name):
        self.name = name
        self.age = None
        self.sex = None


#
def rad2deg(radians):
    degrees = radians * 180 / pi
    return degrees


def deg2rad(degrees):
    radians = degrees * pi / 180
    return radians


def getDistanceBetweenPointsNew(
    latitude1, longitude1, latitude2, longitude2, unit="miles"
):

    theta = longitude1 - longitude2

    distance = (
        60
        * 1.1515
        * rad2deg(
            arccos(
                (sin(deg2rad(latitude1)) * sin(deg2rad(latitude2)))
                + (
                    cos(deg2rad(latitude1))
                    * cos(deg2rad(latitude2))
                    * cos(deg2rad(theta))
                )
            )
        )
    )

    if unit == "miles":
        return round(distance, 2)
    if unit == "kilometers":
        return round(distance * 1.609344, 2)


def sql_connect():
    # Conectando a MariaDB
    try:
        conn = mariadb.connect(
            user="REDACTADO",
            password="REDACTADO",
            host="localhost",
            port="REDACTADO",
            database="REDACTADO",
        )
        print("Connected")

        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)


def extract_arg(arg):
    return arg.split()[1:]


def extract_msg(arg):
    return arg.split()


def get_date():
    return datetime.today().strftime("%Y-%m-%d %H:%M:%S")


def get_tomorrow():
    tomorrow_datetime = datetime.now() + timedelta(days=1)
    return tomorrow_datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_total(ans):
    total_price = 0

    for i in ans:
        total_price += i[2]

    return total_price


def billing(cart, total, userId):
    try:
        conn = sql_connect()
        crsr = conn.cursor()
        crsr.execute(
            f"INSERT INTO Ordenes(idCliente, Total, Fecha, FechaEntrega) VALUES ({userId[0]}, {total}, '{get_date()}', '{get_tomorrow()}')"
        )
        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print(e)
        response = "Lo siento, hubo un error"
        print(response)

        return False


def create_message(ans, total=False):
    text = ""
    total_price = 0

    for i in ans:
        id = i[0]
        product = i[1]
        price = i[2]
        url = i[3]
        text += f" | <b> {str(id)} </b> | <b> {str(product)} </b> | <b> ${str(price)} </b> | {url} \n"

        if total:
            total_price += i[2]

    if total:
        message = (
            "<b>Received 📖 </b> Information about orders:\n\n"
            + text
            + "\n\nTotal: "
            + str(total_price)
        )
    else:
        message = "<b>Received 📖 </b> Information about orders:\n\n" + text

    return message


def send_messages(ans, bot, message):

    response = "<b>Received 📖 </b> Information about orders:\n\n"
    bot.reply_to(message, response, parse_mode="HTML")

    text = ""
    for i in ans:
        id = i[0]
        product = i[1]
        price = i[2]
        url = i[3]
        text += f" | <b> {str(id)} </b> | <b> {str(product)} </b> | <b> ${str(price)} </b> | \n"

        f = open("out.jpg", "wb")
        print("abriendo")
        f.write(urllib.request.urlopen(url).read())
        print("cerrando")
        f.close()

        img = open("out.jpg", "rb")
        bot.send_photo(
            message.chat.id,
            img.read(),
            caption=text,
            reply_to_message_id=message.message_id,
            parse_mode="HTML",
        )
        img.close()

    return


def check_invoice(user, bot):
    text = ""

    try:
        conn = sql_connect()
        crsr = conn.cursor()
        crsr.execute(f"SELECT * FROM Ordenes WHERE idCliente = {user[0]}")
        res = crsr.fetchall()

        for i in res:
            id = i[0]
            idCliente = i[1]
            fecha = i[2]
            price = i[3]
            fecha_entrega = i[4]

            text += f" | <b> {str(id)} </b> | <b> {str(idCliente)} </b> | <b> ${str(fecha)} </b> | <b> ${str(fecha_entrega)} </b> |  <b> ${str(price)} </b> | \n"

        conn.close()
        return text

    except Exception as e:
        print(e)

        return "Error"


def main():

    TOKEN = "<TELEGRAM>:<TOKEN>"
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(regexp=r"/hey|hola|saludos|ayuda/i")
    @bot.message_handler(commands=["help", "start", "hola"])
    def saludar(message):
        print(message)
        bot.reply_to(message, f"Saludos {message.from_user.first_name}, ¿Qué desea?")

    @bot.message_handler(commands=["prueba", "test"])
    def prueba(message):
        bot.reply_to(message, "¿Esto funciona?")

    @bot.message_handler(commands=["productos", "Productos", "PRODUCTOS"])
    def products_with_images(message):
        bot.reply_to(message, "Conectando a la base de datos...")

        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute("SELECT * FROM Productos LIMIT 10")
            res = crsr.fetchall()

            if res:
                send_messages(res, bot, message)
                conn.close()
            else:
                response = "No orders found inside the database."
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["lista", "Lista", "LISTA"])
    def products_list(message):
        bot.reply_to(message, "Conectando a la base de datos...")

        try:

            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute("SELECT * FROM Productos LIMIT 10")
            res = crsr.fetchall()

            if res:
                response = create_message(res)
                print(response, type(response))
                bot.reply_to(message, response, parse_mode="HTML")
                conn.close()
            else:
                response = "No orders found inside the database."
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["detalles", "Detalles", "DETALLES"])
    def products_list(message):
        bot.reply_to(message, "Conectando a la base de datos...")
        args = extract_arg(message.text)

        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute(f"SELECT * FROM Productos WHERE idProductos = {int(args[0])}")
            res = crsr.fetchall()
            print(res)

            if res:
                send_messages(res, bot, message)
                conn.close()
            else:
                response = "No orders found inside the database."
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["registro", "Registro", "REGISTRO"])
    def register_user(message):
        bot.reply_to(message, "Conectando a la base de datos...")
        args = extract_arg(message.text)

        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute(f"SELECT * FROM Cliente WHERE idChat = {message.chat.id}")
            res = crsr.fetchall()
            print(res)

            if res:
                crsr.execute(
                    f"UPDATE Cliente SET Telefono = {args[0]} WHERE idChat = {message.chat.id}"
                )
                conn.commit()
                response = f"Se ha actualizado su número de telefono a {args[0]}"
                bot.reply_to(message, response)
                conn.close()
            else:
                crsr.execute(
                    f"INSERT INTO Cliente (Nombre, Telefono, idChat) VALUES ('{message.from_user.first_name}', '{args[0]}', '{message.chat.id}')"
                )
                conn.commit()
                response = "Se ha registrado exitosamente"
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["reservar", "Reserver", "RESERVAR"])
    def buy_product(message):
        bot.reply_to(message, "Conectando a la base de datos...")
        args = extract_arg(message.text)

        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute(f"SELECT * FROM Cliente WHERE idChat = {message.chat.id}")
            res = crsr.fetchall()
            print(res)

            if res:
                crsr.execute(
                    f"SELECT * FROM Productos WHERE idProductos = {int(args[0])}"
                )
                item = crsr.fetchall()
                if message.chat.id in user_cart_dict:
                    user = user_cart_dict[message.chat.id]
                else:
                    user = UserCart(message.from_user.first_name)

                user.cart.append(item[0])
                user_cart_dict[message.chat.id] = user

                response = f"{item[0][1]} se ha agregado a su carrito"
                bot.reply_to(message, response)
                print(user_cart_dict[message.chat.id].cart)

                conn.close()
            else:
                response = "Para comprar primero debe resgistrarse\nPor favor escriba /registro [Su numero de telefono sin espacios]\nEjemplo /registro 809XXXYYYY"
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["carro", "Carro", "CARRO"])
    def user_cart(message):
        if message.chat.id in user_cart_dict:
            response = create_message(user_cart_dict[message.chat.id].cart, total=True)
            bot.reply_to(message, response, parse_mode="HTML")

            return

        response = "Su carro esta vacio, reserve productos con\n/reservar [Id Del Producto]\nEjemplo\n/reservar 1"
        bot.reply_to(message, response)

    # Laboratorio
    @bot.message_handler(commands=["enviar", "Enviar", "ENVIAR"])
    def buy_item(message):
        bot.reply_to(message, "Conectando a la base de datos...")
        args = extract_arg(message.text)

        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute(f"SELECT * FROM Cliente WHERE idChat = {message.chat.id}")
            res = crsr.fetchall()
            print(res)

            if res:
                userId = res[0]
                sendto = types.ForceReply(selective=False)
                msg = bot.reply_to(message, "Mandame tu ubicacíón", reply_markup=sendto)
                conn.close()
                bot.register_next_step_handler(msg, get_location, userId)

            else:
                response = "Para comprar primero debe resgistrarse\nPor favor escriba /registro [Su numero de telefono sin espacios]\nEjemplo /registro 809XXXYYYY"
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    def get_location(message, userId):

        try:
            location = message.location

            if location is None:
                msg = bot.reply_to(
                    message, "Error tomando la ubicación, por favor envie de nuevo"
                )
                bot.register_next_step_handler(msg, get_location, userId)

                return

            distance = getDistanceBetweenPointsNew(
                TLAT, TLON, location.latitude, location.longitude, "kilometers"
            )

            discount = 0

            if distance > 10:
                msg = bot.reply_to(
                    message, "Disculpe, no enviamos paquetes a más de 10 Kilometros"
                )
                return

            if distance > 5:
                msg = bot.reply_to(
                    message, "Se le aplicará un cargo de 200 por estar a más de 5km"
                )
                discount = 200

            response = "¿Con que desea pagar?"
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add("Tarjeta", "Efectivo")
            msg = bot.reply_to(message, response, reply_markup=markup)
            bot.register_next_step_handler(msg, get_pay, discount, userId)

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)

            return

    def get_pay(message, discount, userId):
        try:
            method = message.text

            if method not in ["Tarjeta", "Efectivo"]:
                msg = bot.reply_to(
                    message, "Error tomando su metodo de pago, por favor envie de nuevo"
                )
                bot.register_next_step_handler(msg, get_pay, discount, userId)

            if method == "Tarjeta":
                total = get_total(user_cart_dict[message.chat.id].cart) - discount

                response = f"¿Acepta esta compra por un total de {total}?"
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add("Acepto", "Cancelar")
                msg = bot.reply_to(message, response, reply_markup=markup)

                bot.register_next_step_handler(msg, get_confirmed, total, userId)

            elif method == "Efectivo":
                total = (
                    get_total(user_cart_dict[message.chat.id].cart) - discount
                ) * decimal.Decimal("0.9")

                response = f"¿Acepta esta compra por un total de {total}?"
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add("Acepto", "Cancelar")
                msg = bot.reply_to(message, response, reply_markup=markup)

                bot.register_next_step_handler(msg, get_confirmed, total, userId)

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)

            return

    def get_confirmed(message, total, userId):
        try:
            confirmation = message.text

            if confirmation not in ["Acepto", "Cancelar"]:
                msg = bot.reply_to(message, "Error al confirmar, intentelo de nuevo")
                bot.register_next_step_handler(msg, get_confirmed, total)

            if confirmation == "Acepto":
                res = billing(user_cart_dict[message.chat.id], total, userId)
                if res:
                    response = (
                        "Su compra se ha efectuado, gracias por confiar en nosotros"
                    )
                    bot.reply_to(message, response)
                    return

                msg = bot.reply_to(message, "Error al confirmar, intentelo de nuevo")
                bot.register_next_step_handler(msg, get_confirmed, total)

            elif confirmation == "Cancelar":
                response = "Compra cancelada"
                bot.reply_to(message, response)

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)

            return

    @bot.message_handler(commands=["zero"])
    def send_invoice(message):
        try:
            conn = sql_connect()
            crsr = conn.cursor()
            crsr.execute(f"SELECT * FROM Cliente WHERE idChat = {message.chat.id}")
            res = crsr.fetchall()

            if res:
                userId = res[0]
                response = check_invoice(userId, bot)
                if response != "Error":
                    bot.reply_to(message, response, parse_mode="HTML")

                    conn.close()
                    return

                bot.reply_to(message, "Ha ocurrido un error", parse_mode="HTML")
                conn.close()

            else:
                response = "Para ver facturas primero comprar y registrarse\nPor favor escriba /registro [Su numero de telefono sin espacios]\nEjemplo /registro 809XXXYYYY"
                bot.reply_to(message, response)
                conn.close()

        except Exception as e:
            print(e)
            response = "Lo siento, hubo un error"
            bot.reply_to(message, response)
            conn.close()

            return

    @bot.message_handler(commands=["prueba"])
    def send_welcome(message):
        msg = bot.reply_to(
            message,
            """\
        Hi there, I am Example bot.
        What's your name?
        """,
        )
        bot.register_next_step_handler(msg, process_name_step)

    def process_name_step(message):
        try:
            chat_id = message.chat.id
            name = message.text
            user = User(name)
            user_dict[chat_id] = user
            msg = bot.reply_to(message, "How old are you?")
            bot.register_next_step_handler(msg, process_age_step)
        except Exception as e:
            bot.reply_to(message, "oooops")

    def process_age_step(message):
        try:
            chat_id = message.chat.id
            age = message.text
            if not age.isdigit():
                msg = bot.reply_to(message, "Age should be a number. How old are you?")
                bot.register_next_step_handler(msg, process_age_step)
                return
            user = user_dict[chat_id]
            user.age = age
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add("Male", "Female")
            msg = bot.reply_to(message, "What is your gender", reply_markup=markup)
            bot.register_next_step_handler(msg, process_sex_step)
        except Exception as e:
            bot.reply_to(message, "oooops")

    def process_sex_step(message):
        try:
            chat_id = message.chat.id
            sex = message.text
            user = user_dict[chat_id]
            if (sex == "Male") or (sex == "Female"):
                user.sex = sex
            else:
                raise Exception("Unknown sex")
            bot.send_message(
                chat_id,
                "Nice to meet you "
                + user.name
                + "\n Age:"
                + str(user.age)
                + "\n Sex:"
                + user.sex,
            )
        except Exception as e:
            bot.reply_to(message, "oooops")

    bot.enable_save_next_step_handlers(delay=2)
    bot.load_next_step_handlers()
    print("Conectado a Telegram!")
    bot.polling()


if __name__ == "__main__":
    main()
