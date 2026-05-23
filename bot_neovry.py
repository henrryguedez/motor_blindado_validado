import logging
import json
import os
import random
import sqlite3 as sl
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    PicklePersistence
)

TOKEN = '8658877853:AAE9MDxujiGgwdvYwNY0BFVmmYNyiPF2U20'
ADMIN_ID = 5747657053
DB_FILE = "leads_neovry.json"
DB_CRM = "nbuilder.db"

LINKS = {
    "ingles": {"url": "https://go.hotmart.com/O97256329R", "beneficio": "Metodologia bilingue acelerada"},
    "reposteria": {"url": "https://neorvry.vercel.app/reposteria.html", "beneficio": "Plantillas de costeo profesional"},
    "canina": {"url": "https://go.hotmart.com/I100829943N", "beneficio": "Guia de adiestramiento en casa"},
    "elite": {"url": "https://hotm.art/activador_elite", "beneficio": "Acceso total al ecosistema Neorvry"}
}

def guardar_lead(user_id, user_data):
    try:
        leads = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                leads = json.load(f)
        user_id_str = str(user_id)
        if user_id_str not in leads:
            leads[user_id_str] = {"fecha_registro": str(datetime.now())}
        leads[user_id_str].update(user_data)
        with open(DB_FILE, "w") as f:
            json.dump(leads, f, indent=4)
        nombre = leads[user_id_str].get("nombre", "Desconocido")
        nicho = user_data.get("nicho") or leads[user_id_str].get("ultimo_nicho", "general")
        status = user_data.get("status", "NUEVO")
        with sl.connect(DB_CRM) as conn:
            ex = conn.execute("SELECT id FROM leads WHERE prefijo=?", (user_id_str,)).fetchone()
            if ex:
                conn.execute("UPDATE leads SET status=?, producto=? WHERE prefijo=?", (status, nicho, user_id_str))
            else:
                conn.execute("INSERT INTO leads (fecha,prefijo,nombre,producto,temperatura,status) VALUES (?,?,?,?,?,?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), user_id_str, nombre, nicho, 70, status))
    except Exception as e:
        print("Error DB: " + str(e))

async def follow_up_callback(context):
    job = context.job
    try:
        msg = "Hola " + job.data["nombre"] + ", tu bono de " + job.data["beneficio"] + " sigue reservado."
        kb = [[InlineKeyboardButton("RECLAMAR BONO", callback_data="elite_reposteria")]]
        await context.bot.send_message(chat_id=job.chat_id, text=msg, reply_markup=InlineKeyboardMarkup(kb))
    except:
        pass

async def start(update, context):
    user = update.effective_user
    kb = [
        [InlineKeyboardButton("Ingles", callback_data="n_ingles"),
         InlineKeyboardButton("Reposteria", callback_data="n_reposteria")],
        [InlineKeyboardButton("Canina", callback_data="n_canina")],
        [InlineKeyboardButton("ACCESO ELITE", callback_data="n_elite")]
    ]
    await update.message.reply_text(
        "SISTEMA NEORVRY v12.1 - Maestro " + user.first_name + ", selecciona tu camino:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_buttons(update, context):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data.startswith("n_"):
        nicho = query.data.split("_")[1]
        guardar_lead(user.id, {"nicho": nicho, "paso": "interesado", "nombre": user.first_name})
        await query.edit_message_text(
            "ANALISIS: " + nicho.upper() + " - Alta demanda detectada. Activa tu Bono de Accion Rapida?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OBTENER ACCESO + BONO", callback_data="pre_" + nicho)]])
        )

    elif query.data.startswith("pre_"):
        nicho = query.data.split("_")[1]
        cupos = random.randint(2, 5)
        await query.edit_message_text(
            "ALERTA: Solo quedan " + str(cupos) + " accesos para " + nicho + ". Confirmas tu compromiso?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("SI ESTOY LISTO", callback_data="elite_" + nicho)]])
        )

    elif query.data.startswith("elite_"):
        nicho = query.data.split("_")[1]
        data = LINKS.get(nicho, LINKS["elite"])
        guardar_lead(user.id, {"status": "CLIC_LINK", "ultimo_nicho": nicho})
        context.job_queue.run_once(follow_up_callback, 86400, chat_id=user.id,
            data={"nombre": user.first_name, "beneficio": data["beneficio"]})
        await query.edit_message_text(
            "ACCESO AUTORIZADO. Bono: " + data["beneficio"],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ACTIVAR AHORA", url=data["url"])]])
        )

async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        with open(DB_FILE, "r") as f:
            leads = json.load(f)
        with sl.connect(DB_CRM) as conn:
            total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        await update.message.reply_text("METRICAS - Leads JSON: " + str(len(leads)) + " | Leads CRM: " + str(total))
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

if __name__ == "__main__":
    persistence = PicklePersistence(filepath="neovry_persistence.pickle")
    app = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("NEORVRY v12.1 OPERANDO CON PUENTE CRM.")
    app.run_polling(drop_pending_updates=True)
