import telebot
import os
import json
import re
import time
from collections import defaultdict
from telebot import types
import atexit
from keep_alive import keep_alive
keep_alive()


# Access the environment variables
API_TOKEN = os.getenv('TOKEN')
OWNER_ID = 6241590270

# Constants
SAVE_DIR = 'saved_files'
SAVE_FILE = os.path.join(SAVE_DIR, 'saved_messages.json')
ADMIN_FILE = os.path.join(SAVE_DIR, 'admins.json')
SCORE_FILE = os.path.join(SAVE_DIR, 'user_scores.json')
LEADERBOARD_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')

# Initialize bot
bot = telebot.TeleBot(API_TOKEN)

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Utility Functions
def extract_mentions(text):
    mention_pattern = re.compile(r'@(\w+)')
    mentions = mention_pattern.findall(text)
    return mentions

def get_user_id_from_username(username):
    user_mapping = {
        'tipsandgamer': '12345',
        'MrRhn': '67890',
    }
    return user_mapping.get(username)

def initialize_leaderboard():
    data = {}
    save_leaderboard(data)
    print("Leaderboard initialized.")

def load_leaderboard():
    if os.path.isfile(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as file:
                data = json.load(file)
                print(f"Loaded leaderboard data: {data}")  # Debugging statement
                return data
        except json.JSONDecodeError:
            print("Error decoding JSON. File may be corrupted or empty.")
            return {}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {}
    else:
        print("Leaderboard file does not exist. Initializing.")
        initialize_leaderboard()
        return {}

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    print("Leaderboard saved.")

def load_saved_messages():
    if os.path.isfile(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error decoding saved messages JSON.")
            return {}
        except Exception as e:
            print(f"An error occurred: {e}")
            return {}
    return {}

def load_admins():
    if os.path.isfile(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error decoding admins JSON.")
            return set()
        except Exception as e:
            print(f"An error occurred: {e}")
            return set()
    return set()

def load_user_scores():
    if os.path.isfile(SCORE_FILE):
        try:
            with open(SCORE_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error decoding user scores JSON.")
            return defaultdict(int)
        except Exception as e:
            print(f"An error occurred: {e}")
            return defaultdict(int)
    return defaultdict(int)

def save_user_scores(scores):
    with open(SCORE_FILE, 'w') as file:
        json.dump(scores, file, indent=4)
    print("User scores saved.")

def save_messages_to_file(messages):
    with open(SAVE_FILE, 'w') as file:
        json.dump(messages, file, indent=4)
    print("Saved messages updated.")

def is_admin(user_id):
    return user_id in admin_user_ids

# Data Initialization
saved_messages = load_saved_messages()
admin_user_ids = load_admins()
user_scores = load_user_scores()
leaderboard = load_leaderboard()

atexit.register(lambda: save_leaderboard(leaderboard))

user_stats = defaultdict(lambda: {
    'username': '',
    'sent_messages': 0,
    'received_replies': 0,
    'received_mentions': 0
})

def update_user_stats(user_id, username=None, sent_messages=0, received_replies=0, received_mentions=0):
    if user_id not in user_stats:
        user_stats[user_id] = {
            'username': username if username else 'Unknown',
            'sent_messages': 0,
            'received_replies': 0,
            'received_mentions': 0
        }

    user = user_stats[user_id]
    if username:
        user['username'] = username
    user['sent_messages'] += sent_messages
    user['received_replies'] += received_replies
    user['received_mentions'] += received_mentions

    save_leaderboard(user_stats)

    print(f"Updated stats for {user['username']}:")
    print(f"Sent Messages: {user['sent_messages']}")
    print(f"Received Replies: {user['received_replies']}")
    print(f"Mentioned: {user['received_mentions']}")

def format_leaderboard(page=1):
    leaderboard = load_leaderboard()
    start_index = (page - 1) * 10
    end_index = start_index + 10
    entries = list(leaderboard.values())[start_index:end_index]
    if not entries:
        return "Leaderboard is currently empty."

    leaderboard_entries = []
    for entry in entries:
        leaderboard_entries.append(
            f"User: {entry['username']}\n"
            f"Sent Messages: {entry['sent_messages']}\n"
            f"Received Replies: {entry['received_replies']}\n"
            f"Mentioned: {entry['received_mentions']}"
        )
    
    return "\n\n".join(leaderboard_entries)

# Command Handlers
@bot.message_handler(commands=['leaderboard'])
def handle_leaderboard(message):
    page = 1
    show_leaderboard(message, page)

@bot.message_handler(commands=['lb'])
def show_leaderboard(message, page=1):
    try:
        formatted_leaderboard = format_leaderboard(page)
        if not formatted_leaderboard.strip():
            formatted_leaderboard = "Leaderboard is currently empty."
        print(f"Sending leaderboard to Telegram:\n{formatted_leaderboard}")  # Debugging statement
        markup = types.InlineKeyboardMarkup()
        if page > 1:
            markup.add(types.InlineKeyboardButton("Previous Page", callback_data=f'prev_{page}'))
        if page * 10 < len(load_leaderboard()):  # Update to use loaded leaderboard
            markup.add(types.InlineKeyboardButton("Next Page", callback_data=f'next_{page}'))
        bot.send_message(message.chat.id, formatted_leaderboard, reply_markup=markup, parse_mode='Markdown')
    except KeyError as e:
        print(f"KeyError: {e} - Leaderboard Data: {load_leaderboard()}")
        bot.send_message(message.chat.id, "An error occurred while formatting the leaderboard.")
    except Exception as e:
        print(f"Exception: {e}")
        bot.send_message(message.chat.id, "An unexpected error occurred.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('next_') or call.data.startswith('prev_'))
def callback_handler(call):
    current_page = int(call.data.split('_')[1])
    new_page = current_page + 1 if call.data.startswith('next_') else max(current_page - 1, 1)
    
    if new_page <= 0 or (new_page - 1) * 10 >= len(load_leaderboard()):  # Use loaded leaderboard
        return
    
    markup = types.InlineKeyboardMarkup()
    if new_page > 1:
        markup.add(types.InlineKeyboardButton("Previous Page", callback_data=f'prev_{new_page}'))
    if new_page * 10 < len(load_leaderboard()):  # Update to use loaded leaderboard
        markup.add(types.InlineKeyboardButton("Next Page", callback_data=f'next_{new_page}'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=format_leaderboard(new_page),
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "Welcome to the bot! Here are the commands you can use:\n"
        "/save <keyword> - Save the message you are replying to with the specified keyword (admin only).\n"
        "/give <keyword> - Retrieve the saved message associated with the specified keyword.\n"
        "/list - List all saved keywords (admin only).\n"
        "/delete <keyword> - Delete the saved message associated with the specified keyword (admin only).\n"
        "/clear - Clear all saved messages (admin only).\n"
        "/ban - Ban a user you reply to (admin only).\n"
        "/unban - Unban a user you reply to (admin only).\n"
        "/mute - Mute a user you reply to (admin only).\n"
        "/unmute - Unmute a user you reply to (admin only).\n"
        "/timeout <minutes> - Timeout a user you reply to for the specified number of minutes (admin only).\n"
        "/slowmode <seconds> - Set slowmode for the chat (admin only).\n"
        "/setadmin <username> - Add a user as admin (admin only).\n"
        "/unsetadmin <username> - Remove a user from admin (admin only).\n"
        "/rules - Display the rules of the chat.\n"
        "/lb or /leaderboard - Display the leaderboard.\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['save'])
def save_message(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    # Check if the message is a reply
    if message.reply_to_message:
        reply_message_id = message.reply_to_message.message_id
    else:
        reply_message_id = None
        print(f"Message {message.message_id} is not a reply.")
        
    # Extract the keyword
    keyword = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not keyword:
        bot.reply_to(message, "Please provide a keyword to save the message.")
        return

    # Save the message with or without the reply message ID
    saved_messages[keyword] = {
        'message_id': reply_message_id,
        'chat_id': message.chat.id
    }
    save_messages_to_file(saved_messages)
    bot.reply_to(message, f"Message saved with keyword '{keyword}'.")

@bot.message_handler(commands=['give'])
def give_message(message):
    keyword = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not keyword:
        bot.reply_to(message, "Please provide a keyword to retrieve the message.")
        return

    message_data = saved_messages.get(keyword)
    if not message_data:
        bot.reply_to(message, f"No message found with keyword '{keyword}'.")
        return

    bot.forward_message(message.chat.id, message_data['chat_id'], message_data['message_id'])

@bot.message_handler(commands=['list'])
def list_keywords(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if not saved_messages:
        bot.reply_to(message, "No saved messages.")
        return

    keywords = "\n".join(saved_messages.keys())
    bot.reply_to(message, f"Saved keywords:\n{keywords}")

@bot.message_handler(commands=['delete'])
def delete_message(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    keyword = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not keyword:
        bot.reply_to(message, "Please provide a keyword to delete the message.")
        return

    if keyword in saved_messages:
        del saved_messages[keyword]
        save_messages_to_file(saved_messages)
        bot.reply_to(message, f"Message with keyword '{keyword}' deleted.")
    else:
        bot.reply_to(message, f"No message found with keyword '{keyword}'.")

@bot.message_handler(commands=['clear'])
def clear_messages(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    saved_messages.clear()
    save_messages_to_file(saved_messages)
    bot.reply_to(message, "All saved messages have been cleared.")

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"User {user_id} has been banned.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.unban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, f"User {user_id} has been unbanned.")

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(message.chat.id, user_id, until_date=int(time.time()) + 3600)
        bot.reply_to(message, f"User {user_id} has been muted for 1 hour.")

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(message.chat.id, user_id, can_send_messages=True)
        bot.reply_to(message, f"User {user_id} has been unmuted.")

@bot.message_handler(commands=['timeout'])
def timeout_user(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        minutes = int(message.text.split(maxsplit=1)[1])
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            bot.restrict_chat_member(message.chat.id, user_id, until_date=int(time.time()) + minutes * 60)
            bot.reply_to(message, f"User {user_id} has been timed out for {minutes} minutes.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Please specify a valid number of minutes.")

@bot.message_handler(commands=['slowmode'])
def slowmode(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        seconds = int(message.text.split(maxsplit=1)[1])
        bot.set_chat_permissions(message.chat.id, can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=True, can_invite_to_group=True, can_pin_messages=True)
        bot.reply_to(message, f"Slowmode set to {seconds} seconds.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Please specify a valid number of seconds.")

@bot.message_handler(commands=['setadmin'])
def set_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        username = message.text.split(maxsplit=1)[1]
        user_id = get_user_id_from_username(username)
        if user_id:
            admin_user_ids.add(user_id)
            with open(ADMIN_FILE, 'w') as file:
                json.dump(list(admin_user_ids), file, indent=4)
            bot.reply_to(message, f"User @{username} has been added as an admin.")
        else:
            bot.reply_to(message, "User not found.")
    except IndexError:
        bot.reply_to(message, "Please provide a username.")

@bot.message_handler(commands=['unsetadmin'])
def unset_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    try:
        username = message.text.split(maxsplit=1)[1]
        user_id = get_user_id_from_username(username)
        if user_id in admin_user_ids:
            admin_user_ids.remove(user_id)
            with open(ADMIN_FILE, 'w') as file:
                json.dump(list(admin_user_ids), file, indent=4)
            bot.reply_to(message, f"User @{username} has been removed as an admin.")
        else:
            bot.reply_to(message, "User is not an admin.")
    except IndexError:
        bot.reply_to(message, "Please provide a username.")

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules = (
        "Rules:\n"
        "1. Be respectful to others.\n"
        "2. No spamming.\n"
        "3. No offensive language.\n"
        "4. Follow all instructions from admins."
    )
    bot.reply_to(message, rules)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Update user stats
    update_user_stats(user_id, username, sent_messages=1)
    
    # Handle replies
    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
        update_user_stats(replied_user_id, received_replies=1)
    
    # Handle mentions
    mentions = extract_mentions(message.text)
    if mentions:
        for mention in mentions:
            mentioned_user_id = get_user_id_from_username(mention)
            if mentioned_user_id:
                update_user_stats(mentioned_user_id, received_mentions=1)

bot.polling(none_stop=True)
